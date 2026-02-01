"""
ClipGenius - Video Editor API Routes
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from pathlib import Path

from models import get_db, Clip
from services.editor import video_editor, TextOverlay, SubtitleStyle


router = APIRouter(prefix="/editor", tags=["editor"])


# ============ Request/Response Schemas ============

class TrimRequest(BaseModel):
    start_time: float = Field(..., ge=0, description="New start time in seconds")
    end_time: float = Field(..., gt=0, description="New end time in seconds")
    filter_name: str = Field("none", description="Optional filter to apply")


class FilterRequest(BaseModel):
    filter_name: str = Field(..., description="Filter to apply")


class TextOverlayRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=200)
    x: str = Field("(w-text_w)/2", description="X position (FFmpeg expression)")
    y: str = Field("h-100", description="Y position (FFmpeg expression)")
    font_size: int = Field(48, ge=12, le=200)
    font_color: str = Field("white")
    start_time: float = Field(0, ge=0)
    end_time: Optional[float] = Field(None)
    background_color: Optional[str] = Field(None)
    background_opacity: float = Field(0.5, ge=0, le=1)


class AddTextOverlaysRequest(BaseModel):
    overlays: List[TextOverlayRequest]


class SubtitleEntry(BaseModel):
    start: float = Field(..., ge=0, description="Start time in seconds")
    end: float = Field(..., gt=0, description="End time in seconds")
    text: str = Field(..., min_length=1)


class SubtitleStyleRequest(BaseModel):
    font_name: str = Field("Arial")
    font_size: int = Field(36, ge=12, le=100)
    primary_color: str = Field("&HFFFFFF")
    outline_color: str = Field("&H000000")
    highlight_color: str = Field("&H00FFFF")
    outline_width: int = Field(2, ge=0, le=10)
    margin_v: int = Field(80, ge=0, le=500)


class UpdateSubtitlesRequest(BaseModel):
    subtitles: List[SubtitleEntry]
    style: Optional[SubtitleStyleRequest] = None


class ApplyEditsRequest(BaseModel):
    trim_start: Optional[float] = Field(None, ge=0)
    trim_end: Optional[float] = Field(None, gt=0)
    filter_name: str = Field("none")
    text_overlays: Optional[List[TextOverlayRequest]] = None
    subtitles: Optional[List[SubtitleEntry]] = None
    subtitle_style: Optional[SubtitleStyleRequest] = None


class FilterInfo(BaseModel):
    id: str
    name: str
    description: str


class VideoInfoResponse(BaseModel):
    duration: float
    width: int
    height: int
    fps: float
    codec: str
    bitrate: int


class EditResponse(BaseModel):
    success: bool
    video_path: str
    message: str
    details: dict = {}


# ============ Endpoints ============

@router.get("/filters", response_model=List[FilterInfo])
async def list_filters():
    """Get list of available video filters"""
    filters = video_editor.get_available_filters()
    return [FilterInfo(**f) for f in filters]


@router.get("/clips/{clip_id}/info", response_model=VideoInfoResponse)
async def get_clip_info(clip_id: int, db: Session = Depends(get_db)):
    """Get video information for a clip"""
    clip = db.query(Clip).filter(Clip.id == clip_id).first()
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")

    video_path = clip.video_path_with_subtitles or clip.video_path
    if not video_path or not Path(video_path).exists():
        raise HTTPException(status_code=404, detail="Video file not found")

    try:
        info = video_editor.get_video_info(video_path)
        return VideoInfoResponse(**info)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get video info: {str(e)}")


@router.post("/clips/{clip_id}/trim", response_model=EditResponse)
async def trim_clip(
    clip_id: int,
    request: TrimRequest,
    db: Session = Depends(get_db)
):
    """Trim a clip to new start/end times"""
    clip = db.query(Clip).filter(Clip.id == clip_id).first()
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")

    # Use original video without subtitles for editing
    video_path = clip.video_path
    if not video_path or not Path(video_path).exists():
        raise HTTPException(status_code=404, detail="Video file not found")

    if request.start_time >= request.end_time:
        raise HTTPException(status_code=400, detail="Start time must be less than end time")

    try:
        result = video_editor.trim_clip(
            input_path=video_path,
            output_name=f"clip_{clip_id}",
            start_time=request.start_time,
            end_time=request.end_time,
            filter_name=request.filter_name
        )

        # Update clip in database
        clip.video_path = result["video_path"]
        clip.duration = result["duration"]
        db.commit()

        return EditResponse(
            success=True,
            video_path=result["video_path"],
            message=f"Clip trimmed successfully ({result['duration']:.1f}s)",
            details=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Trim failed: {str(e)}")


@router.post("/clips/{clip_id}/filter", response_model=EditResponse)
async def apply_filter(
    clip_id: int,
    request: FilterRequest,
    db: Session = Depends(get_db)
):
    """Apply a visual filter to a clip"""
    clip = db.query(Clip).filter(Clip.id == clip_id).first()
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")

    video_path = clip.video_path
    if not video_path or not Path(video_path).exists():
        raise HTTPException(status_code=404, detail="Video file not found")

    try:
        result = video_editor.apply_filter(
            input_path=video_path,
            output_name=f"clip_{clip_id}",
            filter_name=request.filter_name
        )

        # Update clip in database
        clip.video_path = result["video_path"]
        db.commit()

        return EditResponse(
            success=True,
            video_path=result["video_path"],
            message=f"Filter '{request.filter_name}' applied successfully",
            details=result
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Filter failed: {str(e)}")


@router.post("/clips/{clip_id}/text-overlay", response_model=EditResponse)
async def add_text_overlays(
    clip_id: int,
    request: AddTextOverlaysRequest,
    db: Session = Depends(get_db)
):
    """Add text overlays to a clip"""
    clip = db.query(Clip).filter(Clip.id == clip_id).first()
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")

    video_path = clip.video_path
    if not video_path or not Path(video_path).exists():
        raise HTTPException(status_code=404, detail="Video file not found")

    try:
        # Convert request overlays to TextOverlay objects
        overlays = [
            TextOverlay(
                text=o.text,
                x=o.x,
                y=o.y,
                font_size=o.font_size,
                font_color=o.font_color,
                start_time=o.start_time,
                end_time=o.end_time,
                background_color=o.background_color,
                background_opacity=o.background_opacity
            )
            for o in request.overlays
        ]

        result = video_editor.add_text_overlay(
            input_path=video_path,
            output_name=f"clip_{clip_id}",
            overlays=overlays
        )

        # Update clip in database
        clip.video_path = result["video_path"]
        db.commit()

        return EditResponse(
            success=True,
            video_path=result["video_path"],
            message=f"Added {len(overlays)} text overlay(s)",
            details=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Text overlay failed: {str(e)}")


@router.post("/clips/{clip_id}/subtitles", response_model=EditResponse)
async def update_subtitles(
    clip_id: int,
    request: UpdateSubtitlesRequest,
    db: Session = Depends(get_db)
):
    """Update subtitles for a clip"""
    clip = db.query(Clip).filter(Clip.id == clip_id).first()
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")

    video_path = clip.video_path
    if not video_path or not Path(video_path).exists():
        raise HTTPException(status_code=404, detail="Video file not found")

    try:
        # Convert subtitle style if provided
        style = None
        if request.style:
            style = SubtitleStyle(
                font_name=request.style.font_name,
                font_size=request.style.font_size,
                primary_color=request.style.primary_color,
                outline_color=request.style.outline_color,
                highlight_color=request.style.highlight_color,
                outline_width=request.style.outline_width,
                margin_v=request.style.margin_v
            )

        # Convert subtitles to dict format
        subtitle_data = [
            {"start": s.start, "end": s.end, "text": s.text}
            for s in request.subtitles
        ]

        result = video_editor.update_subtitles(
            input_path=video_path,
            output_name=f"clip_{clip_id}",
            subtitle_data=subtitle_data,
            style=style
        )

        # Update clip in database
        clip.video_path_with_subtitles = result["video_path"]
        clip.subtitle_path = result["subtitle_path"]
        db.commit()

        return EditResponse(
            success=True,
            video_path=result["video_path"],
            message=f"Updated {len(subtitle_data)} subtitle(s)",
            details=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Subtitle update failed: {str(e)}")


@router.post("/clips/{clip_id}/apply", response_model=EditResponse)
async def apply_all_edits(
    clip_id: int,
    request: ApplyEditsRequest,
    db: Session = Depends(get_db)
):
    """Apply multiple edits to a clip in a single operation"""
    clip = db.query(Clip).filter(Clip.id == clip_id).first()
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")

    video_path = clip.video_path
    if not video_path or not Path(video_path).exists():
        raise HTTPException(status_code=404, detail="Video file not found")

    # Validate trim times
    if request.trim_start is not None and request.trim_end is not None:
        if request.trim_start >= request.trim_end:
            raise HTTPException(status_code=400, detail="Start time must be less than end time")

    try:
        # Convert text overlays if provided
        text_overlays = None
        if request.text_overlays:
            text_overlays = [
                TextOverlay(
                    text=o.text,
                    x=o.x,
                    y=o.y,
                    font_size=o.font_size,
                    font_color=o.font_color,
                    start_time=o.start_time,
                    end_time=o.end_time,
                    background_color=o.background_color,
                    background_opacity=o.background_opacity
                )
                for o in request.text_overlays
            ]

        # Convert subtitles if provided
        subtitle_data = None
        if request.subtitles:
            subtitle_data = [
                {"start": s.start, "end": s.end, "text": s.text}
                for s in request.subtitles
            ]

        # Convert subtitle style if provided
        subtitle_style = None
        if request.subtitle_style:
            subtitle_style = SubtitleStyle(
                font_name=request.subtitle_style.font_name,
                font_size=request.subtitle_style.font_size,
                primary_color=request.subtitle_style.primary_color,
                outline_color=request.subtitle_style.outline_color,
                highlight_color=request.subtitle_style.highlight_color,
                outline_width=request.subtitle_style.outline_width,
                margin_v=request.subtitle_style.margin_v
            )

        result = video_editor.apply_edits(
            input_path=video_path,
            output_name=f"clip_{clip_id}",
            trim_start=request.trim_start,
            trim_end=request.trim_end,
            filter_name=request.filter_name,
            text_overlays=text_overlays,
            subtitle_data=subtitle_data,
            subtitle_style=subtitle_style
        )

        # Update clip in database
        clip.video_path = result["video_path"]
        if request.trim_start is not None and request.trim_end is not None:
            clip.duration = request.trim_end - request.trim_start
        db.commit()

        return EditResponse(
            success=True,
            video_path=result["video_path"],
            message="All edits applied successfully",
            details=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Edit failed: {str(e)}")


@router.get("/clips/{clip_id}/preview/{timestamp}")
async def get_preview_frame(
    clip_id: int,
    timestamp: float,
    db: Session = Depends(get_db)
):
    """Get a preview frame at the specified timestamp"""
    from fastapi.responses import FileResponse

    clip = db.query(Clip).filter(Clip.id == clip_id).first()
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")

    video_path = clip.video_path
    if not video_path or not Path(video_path).exists():
        raise HTTPException(status_code=404, detail="Video file not found")

    try:
        preview_path = video_editor.generate_preview_frame(
            video_path=video_path,
            timestamp=timestamp,
            output_name=f"clip_{clip_id}_{int(timestamp*1000)}"
        )

        return FileResponse(
            preview_path,
            media_type="image/jpeg",
            filename=f"preview_{clip_id}_{timestamp}.jpg"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Preview generation failed: {str(e)}")
