import urllib.parse
import urllib.request
import json
import xml.etree.ElementTree as ET
from datetime import datetime
from ..openai import openai_client
from ..utils.logging_config import get_logger
from ..db.db_crud.select_db import DBSelect
from ..db.db_crud.insert import DBInsert
from ..db.connector import Connector
from ..cf_recommender.cf_paper_recommender import CFPaperRecommender
from .create_query import CreateQuery

class PaperGenerator:
    def __init__(self):
        self.url = None
        self.model = "gpt-4o-mini"
        self.temperature = 0.0
        self.logger = get_logger(__name__)
        self.db_select = DBSelect()
        self.db_insert = DBInsert()
        self.create_query = CreateQuery()
        self.connector = Connector()
        self.cf_paper_recommender = CFPaperRecommender(self.connector)

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
                
                # Extract published date and year
                published_elem = entry.find('.//{http://www.w3.org/2005/Atom}published')
                if published_elem is not None and published_elem.text:
                    published_str = published_elem.text.strip()
                    paper['published'] = published_str
                    # Extract year from ISO format date (e.g., "2023-01-15T12:00:00Z")
                    try:
                        published_date = datetime.fromisoformat(published_str.replace('Z', '+00:00'))
                        paper['published_year'] = published_date.year
                    except (ValueError, AttributeError):
                        # Try to extract year from string if parsing fails
                        try:
                            paper['published_year'] = int(published_str[:4])
                        except (ValueError, IndexError):
                            paper['published_year'] = None
                else:
                    paper['published'] = 'No date'
                    paper['published_year'] = None
                
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
            # Fetch 15-20 candidates for CF recommendation
            raw_xml = self.search_paper(query, max_results=20)
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

        # 3. Add papers to database and collect paper IDs
        project_id = data['project_id']
        query_id = data.get('query_id') or q.get('query_id')
        
        if not query_id:
            self.logger.warning(f"query_id not found in data or query result, using None")
        
        self.logger.info(f"Adding {len(raw_papers)} papers to database for project {project_id}, query_id {query_id}")
        added_paper_ids = []
        # Map paper_id to original paper data for link and published date
        paper_id_to_raw_data = {}
        
        for idx, paper in enumerate(raw_papers):
            try:
                # Extract paper information
                paper_title = paper.get('title', 'No title')
                paper_summary = paper.get('summary', '')
                published_year = paper.get('published_year')
                pdf_link = paper.get('pdf_link', '')
                arxiv_link = paper.get('link', '')  # ArXiv abstract page link
                published_date = paper.get('published', '')  # Full published date
                authors_list = paper.get('authors', [])
                
                # If we don't have arxiv_link but have pdf_link, generate it
                if not arxiv_link or arxiv_link == 'No link':
                    if pdf_link and pdf_link != 'No PDF':
                        # Convert PDF link to abstract link
                        if '/pdf/' in pdf_link:
                            arxiv_link = pdf_link.replace('/pdf/', '/abs/').replace('.pdf', '')
                        else:
                            arxiv_link = pdf_link
                
                # Skip if paper already exists (check by title)
                # We'll add all papers for now, but you could add duplicate checking here
                
                # Create paper with authors in database
                # Note: We store pdf_link in DB, and generate abstract link from it when needed
                paper_id = self.db_insert.create_paper_with_authors(
                    project_id=project_id,
                    query_id=query_id,
                    paper_title=paper_title,
                    paper_summary=paper_summary,
                    published_year=published_year,
                    pdf_link=pdf_link,
                    authors_list=authors_list
                )
                
                if paper_id:
                    added_paper_ids.append(paper_id)
                    # Store original paper data for link and published date
                    paper_id_to_raw_data[paper_id] = {
                        'link': arxiv_link,
                        'published': published_date
                    }
                    self.logger.info(f"Added paper {idx+1}/{len(raw_papers)}: {paper_title[:50]} (ID: {paper_id})")
                else:
                    self.logger.warning(f"Failed to add paper {idx+1}/{len(raw_papers)}: {paper_title[:50]}")
                    
            except Exception as e:
                self.logger.error(f"Error adding paper {idx+1}/{len(raw_papers)}: {str(e)}", exc_info=True)
                continue
        
        self.logger.info(f"Successfully added {len(added_paper_ids)} papers to database")

        # 4. Use CF recommender to score papers and get top 5
        try:
            self.logger.info(f"Getting CF recommendations for project {project_id}")
            cf_recs = self.cf_paper_recommender.recommend(project_id, topk=5)
            self.logger.info(f"CF recommender returned {len(cf_recs)} recommendations")
            
            if not cf_recs or len(cf_recs) == 0:
                self.logger.warning("CF recommender returned no recommendations, falling back to all papers")
                # Fallback: return all papers without scores
                formatted_papers = []
                for paper_id in added_paper_ids[:5]:  # Limit to 5 even in fallback
                    try:
                        paper_data = self.db_select.get_paper_with_authors(paper_id)
                        if paper_data:
                            authors_list = paper_data.get('authors', [])
                            authors_names = []
                            if isinstance(authors_list, list):
                                for author in authors_list:
                                    if isinstance(author, dict):
                                        authors_names.append(author.get('name', ''))
                                    elif isinstance(author, str):
                                        authors_names.append(author)
                            
                            # Generate ArXiv link from PDF link
                            pdf_link = paper_data.get('pdf_link', '')
                            arxiv_link = ''
                            if pdf_link:
                                # Convert PDF link to abstract link
                                if '/pdf/' in pdf_link:
                                    arxiv_link = pdf_link.replace('/pdf/', '/abs/').replace('.pdf', '')
                                else:
                                    arxiv_link = pdf_link
                            
                            formatted_papers.append({
                                'paper_id': paper_data['paper_id'],
                                'title': paper_data['paper_title'],
                                'paper_title': paper_data['paper_title'],
                                'link': arxiv_link,
                                'pdf_link': pdf_link,
                                'summary': paper_data.get('paper_summary', ''),
                                'paper_summary': paper_data.get('paper_summary', ''),
                                'published_year': paper_data.get('published_year'),
                                'published': f"{paper_data.get('published_year')}-01-01T00:00:00Z" if paper_data.get('published_year') else None,
                                'authors': authors_names,
                                'calculated_score': 0.0
                            })
                    except Exception as e:
                        self.logger.error(f"Error retrieving paper {paper_id}: {str(e)}", exc_info=True)
                        continue
            else:
                # Format CF recommendations for response
                formatted_papers = []
                for rec in cf_recs:
                    paper_id = rec.get('paper_id')
                    pdf_link = rec.get('pdf_link', '')
                    
                    # Get original link and published date if available
                    raw_data = paper_id_to_raw_data.get(paper_id, {})
                    arxiv_link = raw_data.get('link', '')
                    published_date = raw_data.get('published', '')
                    
                    # Generate ArXiv link from PDF link if we don't have it
                    if not arxiv_link or arxiv_link == 'No link':
                        if pdf_link and pdf_link != 'No PDF':
                            if '/pdf/' in pdf_link:
                                arxiv_link = pdf_link.replace('/pdf/', '/abs/').replace('.pdf', '')
                            else:
                                arxiv_link = pdf_link
                    
                    # Use published date from raw data, or generate from year
                    if published_date and published_date != 'No date':
                        published = published_date
                    else:
                        published = f"{rec.get('published_year')}-01-01T00:00:00Z" if rec.get('published_year') else None
                    
                    formatted_papers.append({
                        'paper_id': paper_id,
                        'title': rec.get('paper_title', ''),  # Frontend expects 'title'
                        'paper_title': rec.get('paper_title', ''),
                        'link': arxiv_link,  # ArXiv abstract page for clickable title
                        'pdf_link': pdf_link,
                        'summary': rec.get('paper_summary', ''),  # Frontend expects 'summary'
                        'paper_summary': rec.get('paper_summary', ''),
                        'published_year': rec.get('published_year'),
                        'published': published,
                        'authors': rec.get('authors', []),
                        'calculated_score': rec.get('calculated_score', 0.0)
                    })
                    self.logger.info(f"Recommended paper: {rec.get('paper_title', 'Unknown')[:50]} (score: {rec.get('calculated_score', 0):.4f})")
        
        except Exception as e:
            self.logger.error(f"Failed to get CF recommendations: {str(e)}", exc_info=True)
            # Fallback: return first 5 papers without scoring
            formatted_papers = []
            for paper_id in added_paper_ids[:5]:
                try:
                    paper_data = self.db_select.get_paper_with_authors(paper_id)
                    if paper_data:
                        authors_list = paper_data.get('authors', [])
                        authors_names = []
                        if isinstance(authors_list, list):
                            for author in authors_list:
                                if isinstance(author, dict):
                                    authors_names.append(author.get('name', ''))
                                elif isinstance(author, str):
                                    authors_names.append(author)
                        
                        pdf_link = paper_data.get('pdf_link', '')
                        arxiv_link = ''
                        if pdf_link:
                            if '/pdf/' in pdf_link:
                                arxiv_link = pdf_link.replace('/pdf/', '/abs/').replace('.pdf', '')
                            else:
                                arxiv_link = pdf_link
                        
                        formatted_papers.append({
                            'paper_id': paper_data['paper_id'],
                            'title': paper_data['paper_title'],
                            'paper_title': paper_data['paper_title'],
                            'link': arxiv_link,
                            'pdf_link': pdf_link,
                            'summary': paper_data.get('paper_summary', ''),
                            'paper_summary': paper_data.get('paper_summary', ''),
                            'published_year': paper_data.get('published_year'),
                            'published': f"{paper_data.get('published_year')}-01-01T00:00:00Z" if paper_data.get('published_year') else None,
                            'authors': authors_names,
                            'calculated_score': 0.0
                        })
                except Exception as e2:
                    self.logger.error(f"Error retrieving paper {paper_id}: {str(e2)}", exc_info=True)
                    continue
        
        self.logger.info(f"Returning {len(formatted_papers)} formatted paper recommendations")
        return {
            'papers': formatted_papers,
            'success': True
        }   