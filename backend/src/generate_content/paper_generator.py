import urllib.parse
import urllib.request
import json
from ..openai import openai_client

class PaperGenerator:
    def __init__(self):
        self.url = None

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

    def generate_paper(self, data):
        # 1. Build search query from inputs
        query = f"{data['topic']}; {data['objective']}. "
        if "user_special_instructions" in data:
            query += f" IMPORTANT:{data['user_special_instructions']}"

        # 2. Retrieve papers
        try:
            raw_papers = self.search_youtube_papers(query, max_results=15)
        except Exception as e:
            raise

        # 3. Single LLM call with real data
        # Handle optional fields with defaults
        special_instructions = data.get('user_special_instructions', '')
        past_recommendations = data.get('past_recommendations', '')
        
        prompt = f"""
        Given these Academic papers videos about {data['topic']}:
        {json.dumps(raw_papers, indent=2, ensure_ascii=False)}
        
        Select the 5 most relevant videos based on:
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

if __name__ == '__main__':
    paper_generator = PaperGenerator()
    print(paper_generator.search_paper('machine learning'))