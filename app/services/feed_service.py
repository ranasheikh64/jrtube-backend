import yt_dlp
import json
from app.infrastructure.redis_client import get_cache, set_cache
from app.domain.schemas import VideoSummary

def get_platform_query(query: str, platform: str) -> str:
    if platform.lower() == "tiktok":
        return f"tiktok {query}" if query else "tiktok trending"
    elif platform.lower() == "facebook":
        return f"facebook {query}" if query else "facebook reels"
    return query if query else "trending"

def fetch_youtube_videos(query: str = "", platform: str = "youtube", page: int = 1, limit: int = 10) -> list[VideoSummary]:
    actual_query = get_platform_query(query, platform)
    
    # We fetch a large chunk (50 items) and cache it to simulate pagination
    chunk_size = 50
    cache_key = f"feed:{actual_query}:{chunk_size}"
    
    videos = []
    cached_data = get_cache(cache_key)
    
    if cached_data:
        items = json.loads(cached_data)
        videos = [VideoSummary(**item) for item in items]
    else:
        search_query = f"ytsearch{chunk_size}:{actual_query}"
        ydl_opts = {'extract_flat': True, 'quiet': True, 'nocheckcertificate': True, 'extractor_args': {'youtube': {'player_client': ['android', 'ios']}}}
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(search_query, download=False)
            for entry in result.get('entries', []):
                if not entry: continue
                thumbs = entry.get("thumbnails", [])
                videos.append(VideoSummary(
                    id=entry.get("id", ""),
                    title=entry.get("title", "Unknown"),
                    thumbnail=thumbs[0]["url"] if thumbs else None,
                    url=entry.get("url", ""),
                    duration=entry.get("duration")
                ))

        set_cache(cache_key, json.dumps([v.model_dump() for v in videos]), 3600)
    
    # Pagination Logic
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    return videos[start_idx:end_idx]

def fetch_reels(query: str = "", platform: str = "youtube", page: int = 1, limit: int = 10) -> list[VideoSummary]:
    # Modify query to force short-form content
    base_query = get_platform_query(query, platform)
    if platform.lower() == "youtube":
        actual_query = f"{base_query} #shorts"
    else:
        actual_query = f"{base_query} reels shorts"
        
    chunk_size = 50
    cache_key = f"reels:{actual_query}:{chunk_size}"
    
    videos = []
    cached_data = get_cache(cache_key)
    
    if cached_data:
        items = json.loads(cached_data)
        videos = [VideoSummary(**item) for item in items]
    else:
        search_query = f"ytsearch{chunk_size}:{actual_query}"
        ydl_opts = {'extract_flat': True, 'quiet': True, 'nocheckcertificate': True, 'extractor_args': {'youtube': {'player_client': ['android', 'ios']}}}
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(search_query, download=False)
            for entry in result.get('entries', []):
                if not entry: continue
                
                # Reels/Shorts are typically under 60-70 seconds
                duration = entry.get("duration", 0)
                if duration and duration > 75:
                    continue
                    
                thumbs = entry.get("thumbnails", [])
                videos.append(VideoSummary(
                    id=entry.get("id", ""),
                    title=entry.get("title", "Unknown"),
                    thumbnail=thumbs[0]["url"] if thumbs else None,
                    url=entry.get("url", ""),
                    duration=duration
                ))

        set_cache(cache_key, json.dumps([v.model_dump() for v in videos]), 3600)
    
    # Pagination Logic
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    return videos[start_idx:end_idx]
