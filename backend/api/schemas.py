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
    language: Optional[str] = Field(None, description="Language code for transcription (pt, en, es, auto). Default: pt")


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
    subtitle_data: Optional[List[dict]] = None
    subtitle_file: Optional[str] = None
    has_burned_subtitles: bool = False
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
    """Schema for processing status with detailed progress"""
    project_id: int
    status: str
    progress: int = 0  # 0-100%
    current_step: str = ""
    step_progress: Optional[str] = None  # e.g., "8/15"
    eta_seconds: Optional[int] = None  # Estimated time remaining
    message: str = ""


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


# ============ Output Format Schemas ============

class OutputFormat(BaseModel):
    """Schema for output format"""
    id: str
    name: str
    aspect_ratio: str
    resolution: tuple
    platforms: List[str]
    description: str


class OutputFormatsResponse(BaseModel):
    """Schema for list of available output formats"""
    formats: List[OutputFormat]
    default: str


class ClipExportRequest(BaseModel):
    """Schema for exporting a clip in different format"""
    format_id: str = Field(..., description="Output format ID (vertical, square, landscape, portrait)")


# ============ Editor Schemas ============

class SubtitleWord(BaseModel):
    """Schema for word-level subtitle timing"""
    word: str
    start: float
    end: float


class SubtitleEntryData(BaseModel):
    """Schema for a single subtitle entry"""
    id: str
    start: float
    end: float
    text: str
    words: Optional[List[SubtitleWord]] = None


class SubtitleStyleConfig(BaseModel):
    """Schema for subtitle style configuration"""
    font_name: str = Field("Arial", description="Font family name")
    font_size: int = Field(42, ge=12, le=100, description="Font size in points")
    primary_color: str = Field("&H00FFFFFF", description="Main text color (ASS format)")
    highlight_color: str = Field("&H0000FFFF", description="Highlighted word color for karaoke")
    outline_color: str = Field("&H00000000", description="Text outline color")
    outline_size: int = Field(3, ge=0, le=10, description="Outline thickness")
    shadow_size: int = Field(2, ge=0, le=10, description="Shadow size")
    margin_v: int = Field(80, ge=0, le=500, description="Vertical margin from bottom")
    karaoke_enabled: bool = Field(False, description="Enable karaoke word highlighting")
    scale_effect: bool = Field(False, description="Enable scale pop effect on words")
    # Position settings
    position: str = Field("bottom", description="Subtitle position: top, middle, bottom")
    vertical_offset: int = Field(10, ge=0, le=100, description="Vertical offset from position (0-100%)")


class ClipEditorData(BaseModel):
    """Schema for clip editor data response"""
    clip_id: int
    video_url: str
    video_path: str
    duration: float
    title: Optional[str]
    subtitle_data: List[SubtitleEntryData]
    subtitle_file: Optional[str]
    has_burned_subtitles: bool
    default_style: SubtitleStyleConfig


class UpdateSubtitlesEditorRequest(BaseModel):
    """Schema for updating subtitles from editor"""
    subtitles: List[SubtitleEntryData]
    style: Optional[SubtitleStyleConfig] = None


class ClipExportWithSubtitlesRequest(BaseModel):
    """Schema for exporting clip with subtitle options"""
    include_subtitles: bool = Field(True, description="Whether to burn subtitles into video")
    subtitle_style: Optional[SubtitleStyleConfig] = None
    format_id: str = Field("vertical", description="Output format (vertical, square, landscape)")


class ClipExportResponse(BaseModel):
    """Schema for clip export response"""
    success: bool
    video_path: str
    download_url: str
    message: str
    has_subtitles: bool
    format_id: str
