def yt_tool_spec():
    return {
        "type": "function",
        "function": {
            "name": "search_youtube_videos",
            "description": "Search YouTube for videos relevant to the query and return metadata.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "max_results": {"type": "integer", "minimum": 1, "maximum": 25}
                },
                "required": ["query"]
            }
        }
    }