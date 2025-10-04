from dotenv import load_dotenv

CREATE_QUERY_PROMPT = """
You are a helpful assistant that generates a unique Youtube query based on the following data of a user's project details:
- Objective: {objective}
- Guidelines: {guidelines}

Make sure to generate a unique query that the user has not already searched for:
{get_query_function()}
"""
class CreateQuery:
    def __init__(self):
        pass

    def generate_youtube_query(self, data):
        objective = data['objective']
        guidelines = data['guidelines']
        special_instructions = data['user_special_instructions']