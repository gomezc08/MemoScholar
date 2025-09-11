import os
import requests

YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
YOUTUBE_VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"

def search_youtube_videos(query: str, max_results: int = 10):
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        raise ValueError("Missing YOUTUBE_API_KEY")

    # Step 1: search to get video IDs
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
        results.append({
            "video_title": snippet.get("title"),
            "video_description": snippet.get("description"),
            "video_duration": content.get("duration"),   # ISO8601 e.g. PT14M
            "video_views": stats.get("viewCount"),
            "video_likes": stats.get("likeCount"),
            "video_url": f"https://www.youtube.com/watch?v={v.get('id')}"
        })
    return results