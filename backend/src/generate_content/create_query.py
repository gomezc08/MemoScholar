from dotenv import load_dotenv
from ..openai.openai_client import run_request
from ..db.db_crud.select_db import DBSelect
from ..utils.logging_config import get_logger

CREATE_QUERY_PROMPT = """
You are a helpful assistant that generates a unique Youtube query based on the following data of a user's project details:
- Objective: {objective}
- Guidelines: {guidelines}
Make sure to generate a unique query that the user has not already searched for:
{past_queries}
"""

class CreateQuery:
    def __init__(self):
        self.db_select = DBSelect()
        self.logger = get_logger(__name__)
    def generate_youtube_query(self, data):
        objective = data['objective']
        guidelines = data['guidelines']
        special_instructions = data['user_special_instructions']
        past_queries = self.db_select.get_project_queries(data['project_id'])
        past_queries = '\n'.join([query['queries_text'] for query in past_queries])
        try:
            prompt = CREATE_QUERY_PROMPT.format(objective=objective, guidelines=guidelines, past_queries=past_queries)
            self.logger.info(f"Prompt for generating youtube query: {prompt}")
            response = run_request(prompt)
        except Exception as e:
            self.logger.error(f"Error generating youtube query: {e}")
            return None
        return response

    def generate_paper_query(self, data):
        objective = data['objective']
        guidelines = data['guidelines']
        special_instructions = data['user_special_instructions']
        past_queries = self.db_select.get_project_queries(data['project_id'])
        past_queries = '\n'.join([query['queries_text'] for query in past_queries])
        try:
            prompt = CREATE_QUERY_PROMPT.format(objective=objective, guidelines=guidelines, past_queries=past_queries)
            self.logger.info(f"Prompt for generating paper query: {prompt}")
            response = run_request(prompt)
        except Exception as e:
            self.logger.error(f"Error generating paper query: {e}")
            return None
        return response