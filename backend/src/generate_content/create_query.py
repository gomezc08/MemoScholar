from dotenv import load_dotenv
from ..openai.openai_client import run_request
from ..db.db_crud.select_db import DBSelect
from ..utils.logging_config import get_logger

CREATE_QUERY_PROMPT = """
You are a helpful assistant that generates a **unique {panel_name} search query** based on the user's project information below:

- **Objective:** {objective}
- **Guidelines:** {guidelines}

The goal is to create a concise, general {panel_name} query that helps retrieve a **variety of relevant {panel_name}**, not an overly narrow or academic one.

**Important Requirements:**
1. The query must be **unique** — avoid repeating any of the user's past searches:
   {past_queries}
2. The query should be **broad enough** to yield diverse {panel_name} results (avoid long, over-specified sentences or date ranges).
3. Do **not** include special characters, years, or detailed phrases like "case studies," "implementation details," or "recent advancements."
4. Make sure to include any special instructions in the querythat the user has provided: {special_instructions}

---

### ✅ Good Example Queries
- "machine learning in healthcare"
- "AI applications in patient care"
- "data visualization techniques for researchers"

### ❌ Bad Example Queries
- "Recent advancements in machine learning for medical diagnosis and patient care (2020-2024) with case studies and implementation details"
- "A detailed overview of transformer-based architectures used in clinical NLP pipelines"

Now, generate one **new {panel_name} query** that aligns with the objective and guidelines above.
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
            prompt = CREATE_QUERY_PROMPT.format(objective=objective, guidelines=guidelines, past_queries=past_queries, panel_name="YouTube", special_instructions=special_instructions)
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
            prompt = CREATE_QUERY_PROMPT.format(objective=objective, guidelines=guidelines, past_queries=past_queries, panel_name="Paper", special_instructions=special_instructions)
            self.logger.info(f"Prompt for generating paper query: {prompt}")
            response = run_request(prompt)
        except Exception as e:
            self.logger.error(f"Error generating paper query: {e}")
            return None
        return response