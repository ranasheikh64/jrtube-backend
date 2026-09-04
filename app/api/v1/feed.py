from fastapi import APIRouter, HTTPException, Query
from app.domain.schemas import FeedResponse
from app.services.feed_service import fetch_youtube_videos, fetch_reels

router = APIRouter()

@router.get("/feed", response_model=FeedResponse)
async def get_feed(
    query: str = Query("", description="Search term for the feed"),
    platform: str = Query("youtube", description="Platform filter (youtube, facebook, tiktok)"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=50)
):
    try:
        videos = fetch_youtube_videos(query=query, platform=platform, page=page, limit=limit)
        return FeedResponse(items=videos)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch feed: {str(e)}")

@router.get("/reels", response_model=FeedResponse)
async def get_reels(
    query: str = Query("", description="Search term for the feed"),
    platform: str = Query("youtube", description="Platform filter (youtube, facebook, tiktok)"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=50)
):
    try:
        videos = fetch_reels(query=query, platform=platform, page=page, limit=limit)
        return FeedResponse(items=videos)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch reels: {str(e)}")

@router.get("/search", response_model=FeedResponse)
async def search_videos(
    query: str = Query(..., description="Search term"),
    limit: int = Query(20, ge=1, le=50)
):
    try:
        videos = fetch_youtube_videos(query, limit)
        return FeedResponse(items=videos)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to search: {str(e)}")
