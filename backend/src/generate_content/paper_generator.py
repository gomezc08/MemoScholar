import urllib.parse
import urllib.request
import json
import xml.etree.ElementTree as ET
from ..openai import openai_client
from ..utils.logging_config import get_logger
from ..db.db_crud.select_db import DBSelect
from ..db.connector import Connector
from ..jaccard_coefficient.jaccard_papers import JaccardPaperRecommender
from .create_query import CreateQuery

class PaperGenerator:
    def __init__(self):
        self.url = None
        self.model = "gpt-4o-mini"
        self.temperature = 0.0
        self.logger = get_logger(__name__)
        self.db_select = DBSelect()
        self.create_query = CreateQuery()
        self.connector = Connector()
        self.jaccard_paper_recommender = JaccardPaperRecommender(self.connector)

    def search_paper(self, query: str, max_results: int = 10):
        encoded_query = urllib.parse.quote(query)
        self.url = (
            f"http://export.arxiv.org/api/query?"
            f"search_query={encoded_query}&start=0&max_results={max_results}"
        )
        try:
            r = urllib.request.urlopen(self.url)
            return r.read().decode('utf-8')
        except Exception as e:
            return None

    def parse_arxiv_xml(self, xml_content: str):
        """Parse ArXiv XML response and extract paper data"""
        try:
            root = ET.fromstring(xml_content)
            papers = []
            
            # Find all entry elements
            for entry in root.findall('.//{http://www.w3.org/2005/Atom}entry'):
                paper = {}
                
                # Extract title
                title_elem = entry.find('.//{http://www.w3.org/2005/Atom}title')
                paper['title'] = title_elem.text.strip() if title_elem is not None else 'No title'
                
                # Extract summary
                summary_elem = entry.find('.//{http://www.w3.org/2005/Atom}summary')
                paper['summary'] = summary_elem.text.strip() if summary_elem is not None else 'No summary'
                
                # Extract published date
                published_elem = entry.find('.//{http://www.w3.org/2005/Atom}published')
                paper['published'] = published_elem.text.strip() if published_elem is not None else 'No date'
                
                # Extract authors
                authors = []
                for author in entry.findall('.//{http://www.w3.org/2005/Atom}author/{http://www.w3.org/2005/Atom}name'):
                    authors.append(author.text.strip() if author.text else 'Unknown')
                paper['authors'] = authors
                
                # Extract link to article
                link_elem = entry.find('.//{http://www.w3.org/2005/Atom}link[@rel="alternate"]')
                paper['link'] = link_elem.get('href') if link_elem is not None else 'No link'
                
                # Extract PDF link
                pdf_link_elem = entry.find('.//{http://www.w3.org/2005/Atom}link[@title="pdf"]')
                paper['pdf_link'] = pdf_link_elem.get('href') if pdf_link_elem is not None else 'No PDF'
                
                papers.append(paper)
            
            return papers
        except ET.ParseError as e:
            print(f"XML parsing error: {e}")
            return []
        except Exception as e:
            print(f"Error parsing ArXiv XML: {e}")
            return []

    def _extract_json_from_content(self, content):
        """
        Extract valid JSON from content that may contain comments or extra text.
        """
        # Find the first '{' and the last '}' to extract the JSON object
        start_idx = content.find('{')
        if start_idx == -1:
            return content
        
        # Find the matching closing brace by counting braces
        brace_count = 0
        end_idx = -1
        
        for i in range(start_idx, len(content)):
            if content[i] == '{':
                brace_count += 1
            elif content[i] == '}':
                brace_count -= 1
                if brace_count == 0:
                    end_idx = i
                    break
        
        if end_idx != -1:
            json_content = content[start_idx:end_idx + 1]
            # Remove any JavaScript-style comments (// comments)
            lines = json_content.split('\n')
            cleaned_lines = []
            for line in lines:
                # Remove // comments but preserve // in strings
                comment_pos = -1
                in_string = False
                escape_next = False
                
                for i, char in enumerate(line):
                    if escape_next:
                        escape_next = False
                        continue
                    if char == '\\':
                        escape_next = True
                        continue
                    if char == '"' and not escape_next:
                        in_string = not in_string
                        continue
                    if char == '/' and i + 1 < len(line) and line[i + 1] == '/' and not in_string:
                        comment_pos = i
                        break
                
                if comment_pos != -1:
                    line = line[:comment_pos]
                
                cleaned_lines.append(line)
            
            return '\n'.join(cleaned_lines)
        
        return content

    def generate_paper(self, data, q):
        # 1. query.
        query = q['queries_text']
        if "user_special_instructions" in data:
            query += f" .IMPORTANT:{data['user_special_instructions']}"
        
        self.logger.info(f"Search query: {query}")

        # 2. Retrieve papers
        try:
            self.logger.info(f"Fetching papers from ArXiv with query: {query}")
            raw_xml = self.search_paper(query, max_results=15)
            if not raw_xml:
                self.logger.error("ArXiv API returned no data")
                raise ValueError("Failed to fetch papers from ArXiv")

            # Parse the XML response
            raw_papers = self.parse_arxiv_xml(raw_xml)
            if not raw_papers:
                self.logger.error("No papers found in ArXiv XML response")
                raise ValueError("No papers found in ArXiv response")

            self.logger.info(f"Successfully fetched {len(raw_papers)} papers from ArXiv")

        except Exception as e:
            self.logger.error(f"ArXiv API failed: {str(e)}", exc_info=True)
            raise

        # 3. Format candidates for Jaccard recommender
        self.logger.info("Formatting papers for Jaccard recommender")
        formatted_candidates = []
        for paper in raw_papers:
            formatted_candidates.append({
                'title': paper['title'],
                'summary': paper['summary'],
                'year': paper.get('year'),
                'authors': paper.get('authors', []),
                'pdf_link': paper.get('pdf_link')
            })
        self.logger.info(f"Formatted {len(formatted_candidates)} paper candidates")

        # 4. Add candidates to database and compute features
        try:
            self.logger.info(f"Adding {len(formatted_candidates)} papers to database for project {data['project_id']}")
            added_ids = self.jaccard_paper_recommender.add_candidates(data['project_id'], formatted_candidates)
            self.logger.info(f"Successfully added {len(added_ids)} papers to database with IDs: {added_ids}")
        except Exception as e:
            self.logger.error(f"Failed to add papers to database: {str(e)}", exc_info=True)
            raise

        # 5. Get recommendations from Jaccard coefficient
        try:
            self.logger.info(f"Getting Jaccard recommendations for project {data['project_id']}")
            jaccard_recs = self.jaccard_paper_recommender.recommend(data['project_id'], topk=5, include_likes=True)
            self.logger.info(f"Jaccard recommender returned {len(jaccard_recs)} recommendations")

            # Format recommendations
            formatted_recs = []
            for rec in jaccard_recs:
                formatted_recs.append({
                    'paper_id': rec.get('paper_id'),
                    'paper_title': rec.get('paper_title'),
                    'pdf_link': rec.get('pdf_link'),
                    'calculated_score': rec.get('calculated_score')
                })
                self.logger.info(f"Recommended paper: {rec.get('paper_title')[:50]} (score: {rec.get('calculated_score', 0):.4f})")

            self.logger.info(f"Returning {len(formatted_recs)} formatted paper recommendations")
            return {
                'papers': formatted_recs,
                'success': True
            }
        except Exception as e:
            self.logger.error(f"Failed to get Jaccard recommendations: {str(e)}", exc_info=True)
            return {
                'papers': [],
                'success': False,
                'error': str(e)
            }   