import json
import os
import logging
import requests
import re
from ..openai import openai_client
from ..utils.logging_config import get_logger
from ..db.db_crud.select_db import DBSelect
from ..db.db_crud.insert import DBInsert
from .create_query import CreateQuery
from ..jaccard_coefficient.jaccard_videos import JaccardVideoRecommender
from ..db.connector import Connector

YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
YOUTUBE_VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"

class YoutubeGenerator:
    def __init__(self):
        self.cx = Connector()
        self.model = "gpt-4o-mini"
        self.temperature = 0.0
        self.logger = get_logger(__name__)
        self.db_select = DBSelect()
        self.db_insert = DBInsert()
        self.create_query = CreateQuery()
        self.jaccard_video_recommender = JaccardVideoRecommender(self.cx)
    
    def _safe_encode_string(self, text):
        """Safely encode string for logging by removing/replacing problematic characters"""
        if not text:
            return ""
        # Replace or remove characters that can cause encoding issues
        safe_text = text.encode('ascii', 'ignore').decode('ascii')
        # Truncate if too long
        return safe_text[:200] + "..." if len(safe_text) > 200 else safe_text

    def _parse_iso8601_duration(self, duration_str):
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

    def _avoid_duplicate_videos(self, videos, data):
        if not data.get('project_id'):
            self.logger.info("No project_id provided, skipping duplicate check")
            return videos
            
        # Get past recommendations from both youtube table and youtube_current_recs table
        past_recommendations = self.db_select.get_project_youtube_videos(data['project_id']) or []
        
        # Also check youtube_current_recs for any videos that might be there
        past_current_recs = self.db_select.get_project_youtube_current_recs(data['project_id']) or []
        
        # Combine both sources and extract video titles for comparison
        all_past_videos = past_recommendations + past_current_recs
        past_titles = {rec['video_title'] for rec in all_past_videos}
        
        self.logger.info(f"Found {len(past_titles)} unique past video titles to avoid")
        
        unique_videos = [] 
        for video in videos:
            if video['video_title'] not in past_titles:
                unique_videos.append(video)
            else:
                self.logger.info(f"Skipping duplicate video: {video['video_title']}")
        
        self.logger.info(f"Filtered {len(videos) - len(unique_videos)} duplicate videos, returning {len(unique_videos)} unique videos")
        return unique_videos
    
    def _search_youtube_videos(self, query: str, max_results: int = 10):
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
                parsed_duration = self._parse_iso8601_duration(raw_duration)
                
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

    def generate_youtube_videos(self, data, q):
        # build ai query.
        query = q['queries_text']
        if "user_special_instructions" in data:
            query += f" .IMPORTANT:{data['user_special_instructions']}"
        
        self.logger.info(f"Search query: {query}")
            
        # Call YouTube API directly
        try:
            raw_videos = self._search_youtube_videos(query, max_results=20)
            self.logger.info(f"Successfully fetched {len(raw_videos)} videos from YouTube API")
        except Exception as e:
            self.logger.error(f"YouTube API failed: {str(e)}")
            raise

        unique_videos = self._avoid_duplicate_videos(raw_videos, data)

        # Insert videos into youtube_current_recs table
        if 'project_id' in data and unique_videos:
            try:
                inserted_ids = self.db_insert.insert_youtube_current_recs(data['project_id'], unique_videos)
                self.logger.info(f"Successfully inserted {len(inserted_ids)} videos into youtube_current_recs")
            except Exception as e:
                self.logger.error(f"Failed to insert videos into youtube_current_recs: {str(e)}")
                raise
        
        # Handle optional fields with defaults
        special_instructions = data.get('user_special_instructions', '')

        # get recs from jaccard coefficient
        jaccard_recs = self.jaccard_video_recommender.recommend(data['project_id'], topk=5, include_likes=True)

        # update features
        self.jaccard_video_recommender.update_features(data['project_id'])
        
        # jaccard_recs now returns full video details with score
        formatted_recs = []
        for rec in jaccard_recs:
            # Log without problematic characters to avoid UnicodeEncodeError
            safe_rec = {
                'rec_id': rec.get('rec_id'),
                'video_title': self._safe_encode_string(rec.get('video_title', '')),
                'score': rec.get('calculated_score'),
                'rank_position': rec.get('rank_position')
            }
            self.logger.info(f"Jaccard rec: {safe_rec}")
            # rec is already a dictionary with full video details and score
            formatted_recs.append(rec)
        
        # Log summary without full content to avoid encoding issues
        self.logger.info(f"Returning {len(formatted_recs)} YouTube recommendations")
        
        return {
            'youtube': formatted_recs,
            'success': True
        }