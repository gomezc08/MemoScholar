import json
import os
import requests
import re
from ..openai import openai_client
from ..utils.logging_config import get_logger

YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
YOUTUBE_VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"

class YoutubeGenerator:
    def __init__(self):
        self.model = "gpt-4o-mini"
        self.temperature = 0.0
        self.logger = get_logger(__name__)

    def parse_iso8601_duration(self, duration_str):
        """
        Convert ISO 8601 duration format (PT11M12S) to HH:MM:SS format.
        
        Examples:
        - PT11M12S -> 00:11:12
        - PT1H30M45S -> 01:30:45
        - PT45S -> 00:00:45
        - PT2H -> 02:00:00
        """
        if not duration_str or not duration_str.startswith('PT'):
            return "00:00:00"
        
        # Remove 'PT' prefix
        duration = duration_str[2:]
        
        # Initialize hours, minutes, seconds
        hours = 0
        minutes = 0
        seconds = 0
        
        # Parse hours (H)
        hour_match = re.search(r'(\d+)H', duration)
        if hour_match:
            hours = int(hour_match.group(1))
        
        # Parse minutes (M)
        minute_match = re.search(r'(\d+)M', duration)
        if minute_match:
            minutes = int(minute_match.group(1))
        
        # Parse seconds (S)
        second_match = re.search(r'(\d+)S', duration)
        if second_match:
            seconds = int(second_match.group(1))
        
        # Format as HH:MM:SS
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def search_youtube_videos(self, query: str, max_results: int = 10):
        api_key = os.getenv("YOUTUBE_API_KEY")
        if not api_key:
            raise ValueError("Missing YOUTUBE_API_KEY")

        # Step 1: search to get video IDs
        try:
            r = requests.get(YOUTUBE_SEARCH_URL, params={
                "key": api_key,
                "q": query,
                "part": "snippet",
                "type": "video",
                "maxResults": max_results,
                "safeSearch": "none"
            })
            r.raise_for_status()
            items = r.json().get("items", [])
            
            video_ids = [it["id"]["videoId"] for it in items if "id" in it and "videoId" in it["id"]]
            
            if not video_ids:
                return []

            # Step 2: fetch details for those IDs
            r2 = requests.get(YOUTUBE_VIDEOS_URL, params={
                "key": api_key,
                "id": ",".join(video_ids),
                "part": "snippet,contentDetails,statistics"
            })
            r2.raise_for_status()
            
            results = []
            for v in r2.json().get("items", []):
                snippet = v.get("snippet", {})
                stats = v.get("statistics", {})
                content = v.get("contentDetails", {})
                
                # Parse duration from ISO 8601 to HH:MM:SS format
                raw_duration = content.get("duration", "")
                parsed_duration = self.parse_iso8601_duration(raw_duration)
                
                results.append({
                    "video_title": snippet.get("title"),
                    "video_description": snippet.get("description"),
                    "video_duration": parsed_duration,   # Now in HH:MM:SS format
                    "video_views": stats.get("viewCount"),
                    "video_likes": stats.get("likeCount"),
                    "video_url": f"https://www.youtube.com/watch?v={v.get('id')}"
                })
            
            return results
            
        except requests.RequestException as e:
            raise
        except Exception as e:
            raise

    def generate_youtube_videos(self, data):
        # 1. Build search query from inputs
        query = f"{data['topic']}; {data['objective']}. "
        if "user_special_instructions" in data:
            query += f" IMPORTANT:{data['user_special_instructions']}"
        
        self.logger.info(f"Search query: {query}")
            
        # 2. Call YouTube API directly
        try:
            raw_videos = self.search_youtube_videos(query, max_results=15)
            self.logger.info(f"Successfully fetched {len(raw_videos)} videos from YouTube API")
        except Exception as e:
            self.logger.error(f"YouTube API failed: {str(e)}")
            raise
        
        # 3. Single LLM call with real data
        # Handle optional fields with defaults
        special_instructions = data.get('user_special_instructions', '')
        past_recommendations = data.get('past_recommendations', '')
        
        prompt = f"""
        Given these YouTube videos about {data['topic']}:
        {json.dumps(raw_videos, indent=2, ensure_ascii=False)}
        
        Select the 5 most relevant videos based on:
        - Objective: {data['objective']}
        - Guidelines: {data['guidelines']}
        - Special Instructions: {special_instructions}
        - Avoid duplicates: {past_recommendations}

        IMPORTANT: Make sure to follow the special instructions carefully.
        
        Return JSON in this format: {{"youtube_videos": [...]}}
        """
        
        # 4. Single LLM call
        try:
            response = openai_client.run_request(
                prompt,
                model=self.model,
                temperature=self.temperature
            )
            self.logger.info(f"OpenAI API response success: {response.get('success', False)}")
            self.logger.info(f"Response content length: {len(response.get('content', ''))} characters")
            
            # Parse the JSON content from the response
            content = response.get('content', '')
            if content.startswith('```json'):
                # Remove markdown code block formatting
                content = content.replace('```json', '').replace('```', '').strip()
            
            try:
                parsed_data = json.loads(content)
                # Extract youtube_videos and rename to youtube
                youtube_videos = parsed_data.get('youtube_videos', [])
                return {
                    'youtube': youtube_videos,
                    'success': True
                }
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse JSON content: {str(e)}")
                self.logger.error(f"Content: {content}")
                raise ValueError(f"Invalid JSON response from OpenAI: {str(e)}")
                
        except Exception as e:
            self.logger.error(f"OpenAI API failed: {str(e)}")
            raise