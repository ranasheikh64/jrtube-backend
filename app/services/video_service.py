import yt_dlp
import json
import logging
import base64
import os
from app.infrastructure.redis_client import get_cache, set_cache
from app.domain.schemas import VideoData
from app.core.config import settings

logger = logging.getLogger("uvicorn.error")

def get_cookie_file_path() -> str | None:
    if not settings.YOUTUBE_COOKIES_BASE64:
        return None
    
    cookie_path = "/tmp/youtube_cookies.txt"
    try:
        # Decode base64 to string
        decoded_bytes = base64.b64decode(settings.YOUTUBE_COOKIES_BASE64)
        with open(cookie_path, "wb") as f:
            f.write(decoded_bytes)
        return cookie_path
    except Exception as e:
        logger.error(f"[Cookies] Failed to write cookie file: {e}")
        return None

def extract_segmented_stream(url: str, base_url: str = "http://127.0.0.1:8000") -> dict:
    # Ask for m3u8 formats specifically so we can build a master playlist
    ydl_opts = {
        'format': 'bestvideo[protocol^=m3u8]+bestaudio[protocol^=m3u8]/best[protocol^=m3u8]/best', 
        'quiet': True,
        'noplaylist': True,
        'nocheckcertificate': True,
        'extractor_args': {'youtube': {'player_client': ['ios', 'tv'], 'player_skip': ['webpage', 'configs', 'js']}}
    }
    
    cookie_file = get_cookie_file_path()
    if cookie_file:
        ydl_opts['cookiefile'] = cookie_file
        logger.info("[Scraper] Using YouTube cookies for authentication.")
    
    logger.info(f"[Scraper] Starting yt-dlp extraction for URL: {url}")
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        platform = info.get("extractor_key")
        
        manifest_url = info.get("manifest_url")
        
        if manifest_url:
            logger.info("[Scraper] Found native HLS manifest_url from YouTube.")
            stream_url = manifest_url
            is_hls = True
        else:
            stream_url = info.get("url")
            if stream_url:
                logger.info("[Scraper] No manifest_url found. Falling back to pre-merged format.")
                is_hls = stream_url and ("m3u8" in stream_url or "mpd" in stream_url)
            else:
                logger.info("[Scraper] No pre-merged format found. Generating custom master.m3u8.")
                req_formats = info.get("requested_formats", [])
                if len(req_formats) >= 2:
                    video_url = req_formats[0].get("url")
                    audio_url = req_formats[1].get("url")
                    
                    m3u8_content = f"""#EXTM3U
#EXT-X-MEDIA:TYPE=AUDIO,GROUP-ID="audio_1",NAME="Default",DEFAULT=YES,AUTOSELECT=YES,URI="{audio_url}"
#EXT-X-STREAM-INF:BANDWIDTH=2500000,RESOLUTION=1280x720,AUDIO="audio_1"
{video_url}
"""
                    set_cache(f"m3u8:{url}", m3u8_content, 7200)
                    stream_url = f"{base_url}{settings.API_V1_STR}/videos/master.m3u8?video_url={url}"
                    is_hls = True
                else:
                    logger.error("[Scraper] No formats available.")
                    stream_url = ""
                    is_hls = False
            
        logger.info(f"[Scraper] Successfully extracted stream for {platform}. Is HLS? {is_hls}")
        
        return {
            "title": info.get("title"),
            "thumbnail": info.get("thumbnail"),
            "stream_url": stream_url,
            "is_hls": is_hls,
            "source_platform": platform
        }

def resolve_video_service(video_url: str, force_refresh: bool, base_url: str = "http://127.0.0.1:8000") -> VideoData:
    cache_key = f"vid:{video_url}"
    logger.info(f"[VideoPlayer] Playback requested for: {video_url} | force_refresh={force_refresh}")
    
    if not force_refresh:
        cached_data = get_cache(cache_key)
        if cached_data:
            logger.info(f"[VideoPlayer] Cache HIT for {video_url}.")
            data_dict = json.loads(cached_data)
            return VideoData(**data_dict)
            
    logger.info(f"[VideoPlayer] Cache MISS or force_refresh is true.")
    extracted = extract_segmented_stream(video_url, base_url)
    video_data = VideoData(**extracted)
    set_cache(cache_key, video_data.model_dump_json(), settings.CACHE_TTL_SECONDS)
    return video_data

def get_video_formats(url: str) -> list:
    cache_key = f"formats:{url}"
    cached = get_cache(cache_key)
    if cached:
        return json.loads(cached)

    ydl_opts = {
        'quiet': True,
        'noplaylist': True,
        'nocheckcertificate': True,
        'extractor_args': {'youtube': {'player_client': ['ios', 'tv'], 'player_skip': ['webpage', 'configs', 'js']}}
    }
    
    cookie_file = get_cookie_file_path()
    if cookie_file:
        ydl_opts['cookiefile'] = cookie_file
        
    logger.info(f"[Scraper] Extracting formats for URL: {url}")
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        formats = info.get("formats", [])
        
        extracted_formats = []
        for f in formats:
            # We want direct URLs for downloading (mp4, m4a). Ignore m3u8 playlists.
            if f.get("protocol") in ["http", "https"] and f.get("ext") in ["mp4", "m4a", "webm"]:
                format_info = {
                    "format_id": f.get("format_id"),
                    "resolution": f.get("format_note") or f.get("resolution") or "Audio",
                    "ext": f.get("ext"),
                    "filesize": f.get("filesize") or f.get("filesize_approx") or 0,
                    "url": f.get("url"),
                    "vcodec": f.get("vcodec", "none"),
                    "acodec": f.get("acodec", "none")
                }
                
                # Basic filter: must have some size or be explicitly audio/video
                if format_info["filesize"] > 0 or format_info["vcodec"] != "none" or format_info["acodec"] != "none":
                    extracted_formats.append(format_info)
                else:
                    logger.warning(f"[Scraper] Skipped format {f.get('format_id')} due to zero filesize or no codec.")
            else:
                logger.debug(f"[Scraper] Ignored format {f.get('format_id')} with protocol {f.get('protocol')} and ext {f.get('ext')}.")
        
        logger.info(f"[Scraper] Successfully extracted {len(extracted_formats)} usable formats for {url}")
        
        # Sort by filesize descending
        extracted_formats.sort(key=lambda x: x["filesize"], reverse=True)
        
        # Cache for 1 hour
        set_cache(cache_key, json.dumps(extracted_formats), 3600)
        return extracted_formats
