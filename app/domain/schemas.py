from pydantic import BaseModel
from typing import Optional

class VideoData(BaseModel):
    title: Optional[str] = None
    thumbnail: Optional[str] = None
    stream_url: str
    is_hls: bool = False
    source_platform: Optional[str] = "unknown"

class ResolveRequest(BaseModel):
    video_url: str
    force_refresh: bool = False

class VideoSummary(BaseModel):
    id: str
    title: str
    thumbnail: Optional[str] = None
    url: str
    duration: Optional[int] = None

class FeedResponse(BaseModel):
    items: list[VideoSummary]
