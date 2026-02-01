"""
ClipGenius - Pydantic Schemas
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, HttpUrl


# ============ Request Schemas ============

class ProjectCreate(BaseModel):
    """Schema for creating a new project"""
    url: str = Field(..., description="YouTube video URL")


class ClipRegenerate(BaseModel):
    """Schema for regenerating a clip"""
    start_time: Optional[float] = Field(None, description="New start time in seconds")
    end_time: Optional[float] = Field(None, description="New end time in seconds")


# ============ Response Schemas ============

class ClipResponse(BaseModel):
    """Schema for clip response"""
    id: int
    project_id: int
    start_time: float
    end_time: float
    duration: Optional[float]
    title: Optional[str]
    viral_score: Optional[float]
    score_justification: Optional[str]
    video_path: Optional[str]
    video_path_with_subtitles: Optional[str]
    subtitle_path: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProjectResponse(BaseModel):
    """Schema for project response"""
    id: int
    youtube_url: str
    youtube_id: str
    title: Optional[str]
    duration: Optional[int]
    thumbnail_url: Optional[str]
    status: str
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime
    clips_count: int = 0

    class Config:
        from_attributes = True


class ProjectDetailResponse(ProjectResponse):
    """Schema for project detail response with clips"""
    clips: List[ClipResponse] = []


class ProcessingStatus(BaseModel):
    """Schema for processing status"""
    project_id: int
    status: str
    progress: Optional[int] = None  # 0-100
    current_step: Optional[str] = None
    message: Optional[str] = None


# ============ List Responses ============

class ProjectListResponse(BaseModel):
    """Schema for paginated project list"""
    items: List[ProjectResponse]
    total: int
    page: int
    per_page: int


class ClipListResponse(BaseModel):
    """Schema for clip list"""
    items: List[ClipResponse]
    total: int
