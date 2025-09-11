from ..openai import openai_client
from .resources.tool_specs import yt_tool_spec
from .resources.system_call import system_call
from ..integrations.youtube_api import search_youtube_videos

YOTUBE_PROMPT = """
You are a helpful assistant that will use the following information to retrieve 10 relevant Youtube videos to a user.

## Inputs
1. Here is the user's research topic:
<topic>
{topic}
</topic>

2. Here is the user's research objective:
<objective>
{objective}
</objective>

3. Here is the user's research guidelines:
<guidelines>
{guidelines}
</guidelines>

4. (Optional) VERY IMPORTANT: Here is the user's special instructions. Please follow these instructions carefully and use them as the main guideline for the recommendation.
<special_instructions>
{special_instructions}
</special_instructions>

## Special Instructions (IMPORTANT)
- Make sure to recommend videos that are relevant to the user's research topic, objective, and guidelines.
- Make sure to follow the user's special instructions VERY CAREFULLY.
- Make sure NOT to recommend videos that are already recommended in the past.
<past_recommendations>
{past_recommendations}
</past_recommendations>

## Deliverable
You should return the list of recommended videos in the following format:
{json.dumps({
    "youtube_videos": [
        {
            "video_title": "video_title",
            "video_description": "video_description",
            "video_duration": "video_duration",
            "video_views": "video_views",
            "video_likes": "video_likes",
            "video_url": "video_url"
        }
    ]
})}
"""

class YoutubeGenerator:
    def __init__(self):
        self.model = "gpt-4o-mini"
        self.temperature = 0.0
        self.yt_tool_spec = yt_tool_spec()
        # TODO: add other tool specs.
        self.tool_registry = {
            "search_youtube_videos": search_youtube_videos
        }
    def generate_youtube_videos(self, data):
        # initialize variables.
        topic = data['topic']
        objective = data['objective']
        guidelines = data['guidelines']
        special_instructions = data['special_instructions']
        past_recommendations = data['past_recommendations']
        
        # format the prompt.
        prompt = YOTUBE_PROMPT.format (
            topic=topic, 
            objective=objective, 
            guidelines=guidelines, 
            special_instructions=special_instructions, 
            past_recommendations=past_recommendations
        )

        # format the messages.
        messages = [
            {"role": "system", "content": system_call()},
            {"role": "user", "content": prompt}
        ]

        # call the LLM.
        try:
            response = openai_client.run_request(
                messages, 
                tools=[self.yt_tool_spec],      # TODO: add other tool specs.
                tool_registry=self.tool_registry,
                model=self.model,
                temperature=self.temperature,
                max_tokens=2000
            )
            print(f"Youtube videos are generated successfully: {response}")
            return response

        except Exception as e:
            print(f"Error generating youtube videos: {e}")
            return None

        