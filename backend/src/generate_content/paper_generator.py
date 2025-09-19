import urllib.parse
import urllib.request
import json
import xml.etree.ElementTree as ET
from ..openai import openai_client

class PaperGenerator:
    def __init__(self):
        self.url = None
        self.model = "gpt-4o-mini"
        self.temperature = 0.0

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

    def generate_paper(self, data):
        # 1. Build search query from inputs
        query = f"{data['topic']}; {data['objective']}. "
        if "user_special_instructions" in data:
            query += f" IMPORTANT:{data['user_special_instructions']}"

        # 2. Retrieve papers
        try:
            raw_xml = self.search_paper(query, max_results=15)
            if not raw_xml:
                raise ValueError("Failed to fetch papers from ArXiv")
            
            # Parse the XML response
            raw_papers = self.parse_arxiv_xml(raw_xml)
            if not raw_papers:
                raise ValueError("No papers found in ArXiv response")
                
        except Exception as e:
            raise

        # 3. Single LLM call with real data
        # Handle optional fields with defaults
        special_instructions = data.get('user_special_instructions', '')
        past_recommendations = data.get('past_recommendations', '')
        
        prompt = f"""
        Given these Academic papers about {data['topic']}:
        {json.dumps(raw_papers, indent=2, ensure_ascii=False)}
        
        Select the 5 most relevant papers based on:
        - Objective: {data['objective']}
        - Guidelines: {data['guidelines']}
        - Special Instructions: {special_instructions}
        - Avoid duplicates: {past_recommendations}

        IMPORTANT: Make sure to follow the special instructions carefully.
        
        Return JSON in this format: {{"papers": [...]}}
        """
        
        # 4. Single LLM call
        try:
            response = openai_client.run_request(
                prompt,
                model=self.model,
                temperature=self.temperature
            )
            
            # Parse the JSON content from the response
            content = response.get('content', '')
            if content.startswith('```json'):
                # Remove markdown code block formatting
                content = content.replace('```json', '').replace('```', '').strip()
            
            try:
                parsed_data = json.loads(content)
                # Extract papers and rename to papers
                papers = parsed_data.get('papers', [])
                return {
                    'papers': papers,
                    'success': True
                }
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON response from OpenAI: {str(e)}")
                
        except Exception as e:
            raise   