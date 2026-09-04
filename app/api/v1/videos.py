from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
from app.domain.schemas import VideoData
from app.services.video_service import resolve_video_service
from app.infrastructure.redis_client import get_cache

router = APIRouter()

@router.get("/resolve", response_model=VideoData)
async def resolve_video(
    video_url: str = Query(..., description="The URL of the video to resolve"),
    force_refresh: bool = Query(False, description="Bypass cache and force a new scrape")
):
    try:
        return resolve_video_service(video_url, force_refresh)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to resolve video: {str(e)}")

@router.get("/formats")
async def get_formats(video_url: str):
    try:
        from app.services.video_service import get_video_formats
        formats = get_video_formats(video_url)
        return {"formats": formats}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch formats: {str(e)}")

@router.get("/master.m3u8")
async def get_master_playlist(video_url: str):
    m3u8_content = get_cache(f"m3u8:{video_url}")
    if not m3u8_content:
        raise HTTPException(status_code=404, detail="M3U8 playlist expired or not found. Please resolve the video again.")
    
    return Response(content=m3u8_content, media_type="application/vnd.apple.mpegurl")
