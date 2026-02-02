"""
ClipGenius - Video Editor API Routes
"""
import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from pathlib import Path

from models import get_db, Clip
from services.editor import video_editor, TextOverlay, SubtitleStyle
from services.subtitler_v2 import SubtitleGeneratorV2  # V2: tamanho consistente
from config import CLIPS_DIR, OUTPUT_FORMATS
from .schemas import (
    ClipEditorData,
    SubtitleEntryData,
    SubtitleStyleConfig,
    UpdateSubtitlesEditorRequest,
    ClipExportWithSubtitlesRequest,
    ClipExportResponse,
)

router = APIRouter(prefix="/editor", tags=["editor"])

# Initialize subtitle generator V2
subtitler = SubtitleGeneratorV2()  # V2: tamanho consistente e melhor sincronização


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
    position: str = Field("bottom", description="Subtitle position: top, middle, bottom")
    vertical_offset: int = Field(10, ge=0, le=100, description="Vertical offset from position")


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


# ============ Layer-Based Editor Endpoints ============

@router.get("/clips/{clip_id}/editor-data", response_model=ClipEditorData)
async def get_clip_editor_data(
    clip_id: int,
    db: Session = Depends(get_db)
):
    """
    Get clip data for the layer-based editor.
    Returns video URL and subtitle data for overlay rendering.
    """
    clip = db.query(Clip).filter(Clip.id == clip_id).first()
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")

    # Get video path (prefer without burned subtitles for editing)
    video_path = clip.video_path
    if not video_path or not Path(video_path).exists():
        raise HTTPException(status_code=404, detail="Video file not found")

    # Build video URL
    filename = Path(video_path).name
    video_url = f"/clips/{filename}"

    # Parse subtitle_data if it's a string
    subtitle_data = clip.subtitle_data
    if isinstance(subtitle_data, str):
        try:
            subtitle_data = json.loads(subtitle_data)
        except json.JSONDecodeError:
            subtitle_data = []

    # Default style configuration (karaoke disabled by default)
    default_style = SubtitleStyleConfig(
        font_name="Arial",
        font_size=42,
        primary_color="&H00FFFFFF",
        highlight_color="&H0000FFFF",
        outline_color="&H00000000",
        outline_size=3,
        shadow_size=2,
        margin_v=80,
        karaoke_enabled=False,  # Disabled by default
        scale_effect=False,      # Disabled by default
        position="bottom",
        vertical_offset=10
    )

    return ClipEditorData(
        clip_id=clip.id,
        video_url=video_url,
        video_path=video_path,
        duration=clip.duration or 0,
        title=clip.title,
        subtitle_data=[SubtitleEntryData(**s) for s in (subtitle_data or [])],
        subtitle_file=clip.subtitle_file,
        has_burned_subtitles=clip.has_burned_subtitles or False,
        default_style=default_style
    )


@router.get("/clips/{clip_id}/subtitle-file")
async def get_clip_subtitle_file(
    clip_id: int,
    db: Session = Depends(get_db)
):
    """
    Download the .ass subtitle file for a clip.
    """
    clip = db.query(Clip).filter(Clip.id == clip_id).first()
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")

    subtitle_file = clip.subtitle_file or clip.subtitle_path
    if not subtitle_file or not Path(subtitle_file).exists():
        raise HTTPException(status_code=404, detail="Subtitle file not found")

    return FileResponse(
        subtitle_file,
        media_type="text/plain",
        filename=f"clip_{clip_id}_subtitles{Path(subtitle_file).suffix}"
    )


@router.put("/clips/{clip_id}/editor-subtitles")
async def update_clip_subtitles_editor(
    clip_id: int,
    request: UpdateSubtitlesEditorRequest,
    db: Session = Depends(get_db)
):
    """
    Update subtitle data from the editor.
    Saves the subtitle data and regenerates the .ass file without burning.
    """
    clip = db.query(Clip).filter(Clip.id == clip_id).first()
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")

    try:
        # Convert subtitles to dict format for storage
        subtitle_data = [s.model_dump() for s in request.subtitles]

        # Update clip subtitle data
        clip.subtitle_data = subtitle_data

        # Regenerate .ass file with new data
        if subtitle_data:
            # Extract all words from subtitle entries
            all_words = []
            for entry in subtitle_data:
                words = entry.get('words', [])
                if words:
                    all_words.extend(words)
                else:
                    # Create word entries from text
                    text = entry.get('text', '')
                    start = entry.get('start', 0)
                    end = entry.get('end', 0)
                    word_list = text.split()
                    if word_list:
                        duration_per_word = (end - start) / len(word_list)
                        for j, word in enumerate(word_list):
                            all_words.append({
                                'word': word,
                                'start': start + j * duration_per_word,
                                'end': start + (j + 1) * duration_per_word
                            })

            # Generate new ASS file
            output_name = f"clip_{clip_id}"
            ass_path = CLIPS_DIR / f"{output_name}.ass"

            # Build style dict if provided
            style = None
            if request.style:
                style = {
                    'font_name': request.style.font_name,
                    'font_size': request.style.font_size,
                    'primary_color': request.style.primary_color,
                    'outline_color': request.style.outline_color,
                    'outline': request.style.outline_size,
                    'shadow': request.style.shadow_size,
                    'margin_v': request.style.margin_v,
                }

            karaoke_enabled = request.style.karaoke_enabled if request.style else True

            if karaoke_enabled:
                subtitler.generate_ass_karaoke(
                    words=all_words,
                    output_path=str(ass_path),
                    offset=0,
                    style=style
                )
            else:
                subtitler.generate_ass(
                    words=all_words,
                    output_path=str(ass_path),
                    offset=0,
                    style=style
                )

            clip.subtitle_file = str(ass_path)
            clip.subtitle_path = str(ass_path)

        db.commit()

        return {
            "success": True,
            "message": f"Updated {len(subtitle_data)} subtitle(s)",
            "subtitle_file": clip.subtitle_file
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update subtitles: {str(e)}")


@router.post("/clips/{clip_id}/export-with-subtitles", response_model=ClipExportResponse)
async def export_clip_with_subtitles(
    clip_id: int,
    request: ClipExportWithSubtitlesRequest,
    db: Session = Depends(get_db)
):
    """
    Export a clip with optional subtitle burning.
    User can choose to include or exclude subtitles in the final video.
    """
    clip = db.query(Clip).filter(Clip.id == clip_id).first()
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")

    video_path = clip.video_path
    if not video_path or not Path(video_path).exists():
        raise HTTPException(status_code=404, detail="Video file not found")

    # Validate format
    if request.format_id not in OUTPUT_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid format. Available: {', '.join(OUTPUT_FORMATS.keys())}"
        )

    try:
        output_name = f"clip_{clip_id}_export_{request.format_id}"
        output_path = CLIPS_DIR / f"{output_name}.mp4"

        if request.include_subtitles:
            # Get subtitle data
            subtitle_data = clip.subtitle_data
            if isinstance(subtitle_data, str):
                subtitle_data = json.loads(subtitle_data)

            if not subtitle_data:
                raise HTTPException(status_code=400, detail="No subtitle data available")

            # Build style dict if provided
            style = None
            if request.subtitle_style:
                style = {
                    'font_name': request.subtitle_style.font_name,
                    'font_size': request.subtitle_style.font_size,
                    'primary_color': request.subtitle_style.primary_color,
                    'outline_color': request.subtitle_style.outline_color,
                    'outline': request.subtitle_style.outline_size,
                    'shadow': request.subtitle_style.shadow_size,
                    'margin_v': request.subtitle_style.margin_v,
                }
                karaoke_enabled = request.subtitle_style.karaoke_enabled
            else:
                karaoke_enabled = True

            # Burn subtitles on demand
            result = subtitler.burn_subtitles_on_demand(
                video_path=video_path,
                subtitle_data=subtitle_data,
                output_path=str(output_path),
                style=style,
                enable_karaoke=karaoke_enabled
            )

            export_path = result['path']
            has_subtitles = True
            message = "Clip exportado com legendas"
        else:
            # Copy video without subtitles
            import shutil
            shutil.copy2(video_path, output_path)
            export_path = str(output_path)
            has_subtitles = False
            message = "Clip exportado sem legendas"

        # Build download URL
        filename = Path(export_path).name
        download_url = f"/clips/{filename}"

        return ClipExportResponse(
            success=True,
            video_path=export_path,
            download_url=download_url,
            message=message,
            has_subtitles=has_subtitles,
            format_id=request.format_id
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


# ============ Bulk Operations ============

class BulkExportRequest(BaseModel):
    clip_ids: List[int] = Field(..., min_length=1, description="List of clip IDs to export")
    format_id: str = Field("vertical", description="Output format (vertical, square, landscape)")
    include_subtitles: bool = Field(True, description="Whether to include subtitles")
    subtitle_style: Optional[SubtitleStyleConfig] = None


class BulkDeleteRequest(BaseModel):
    clip_ids: List[int] = Field(..., min_length=1, description="List of clip IDs to delete")


class BulkApplyStyleRequest(BaseModel):
    clip_ids: List[int] = Field(..., min_length=1, description="List of clip IDs")
    subtitle_style: SubtitleStyleConfig = Field(..., description="Style to apply")


class BulkOperationResult(BaseModel):
    success: bool
    total: int
    processed: int
    failed: int
    results: List[dict]
    message: str


@router.post("/clips/bulk-export", response_model=BulkOperationResult)
async def bulk_export_clips(
    request: BulkExportRequest,
    db: Session = Depends(get_db)
):
    """
    Export multiple clips at once.
    Returns a list of export results for each clip.
    """
    results = []
    processed = 0
    failed = 0

    # Validate format
    if request.format_id not in OUTPUT_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid format. Available: {', '.join(OUTPUT_FORMATS.keys())}"
        )

    for clip_id in request.clip_ids:
        try:
            clip = db.query(Clip).filter(Clip.id == clip_id).first()
            if not clip:
                results.append({
                    "clip_id": clip_id,
                    "success": False,
                    "error": "Clip not found"
                })
                failed += 1
                continue

            video_path = clip.video_path
            if not video_path or not Path(video_path).exists():
                results.append({
                    "clip_id": clip_id,
                    "success": False,
                    "error": "Video file not found"
                })
                failed += 1
                continue

            output_name = f"clip_{clip_id}_export_{request.format_id}"
            output_path = CLIPS_DIR / f"{output_name}.mp4"

            if request.include_subtitles:
                subtitle_data = clip.subtitle_data
                if isinstance(subtitle_data, str):
                    subtitle_data = json.loads(subtitle_data)

                if subtitle_data:
                    style = None
                    if request.subtitle_style:
                        style = {
                            'font_name': request.subtitle_style.font_name,
                            'font_size': request.subtitle_style.font_size,
                            'primary_color': request.subtitle_style.primary_color,
                            'outline_color': request.subtitle_style.outline_color,
                            'outline': request.subtitle_style.outline_size,
                            'shadow': request.subtitle_style.shadow_size,
                            'margin_v': request.subtitle_style.margin_v,
                        }
                        karaoke_enabled = request.subtitle_style.karaoke_enabled
                    else:
                        karaoke_enabled = False

                    result = subtitler.burn_subtitles_on_demand(
                        video_path=video_path,
                        subtitle_data=subtitle_data,
                        output_path=str(output_path),
                        style=style,
                        enable_karaoke=karaoke_enabled
                    )
                    export_path = result['path']
                else:
                    import shutil
                    shutil.copy2(video_path, output_path)
                    export_path = str(output_path)
            else:
                import shutil
                shutil.copy2(video_path, output_path)
                export_path = str(output_path)

            filename = Path(export_path).name
            download_url = f"/clips/{filename}"

            results.append({
                "clip_id": clip_id,
                "success": True,
                "download_url": download_url,
                "video_path": export_path
            })
            processed += 1

        except Exception as e:
            results.append({
                "clip_id": clip_id,
                "success": False,
                "error": str(e)
            })
            failed += 1

    return BulkOperationResult(
        success=failed == 0,
        total=len(request.clip_ids),
        processed=processed,
        failed=failed,
        results=results,
        message=f"Exported {processed} of {len(request.clip_ids)} clips"
    )


@router.post("/clips/bulk-delete", response_model=BulkOperationResult)
async def bulk_delete_clips(
    request: BulkDeleteRequest,
    db: Session = Depends(get_db)
):
    """
    Delete multiple clips at once.
    """
    results = []
    processed = 0
    failed = 0

    for clip_id in request.clip_ids:
        try:
            clip = db.query(Clip).filter(Clip.id == clip_id).first()
            if not clip:
                results.append({
                    "clip_id": clip_id,
                    "success": False,
                    "error": "Clip not found"
                })
                failed += 1
                continue

            # Delete video files
            for path_attr in ['video_path', 'video_path_with_subtitles', 'subtitle_path', 'subtitle_file']:
                path = getattr(clip, path_attr, None)
                if path and Path(path).exists():
                    try:
                        Path(path).unlink()
                    except Exception:
                        pass

            # Delete from database
            db.delete(clip)
            db.commit()

            results.append({
                "clip_id": clip_id,
                "success": True
            })
            processed += 1

        except Exception as e:
            db.rollback()
            results.append({
                "clip_id": clip_id,
                "success": False,
                "error": str(e)
            })
            failed += 1

    return BulkOperationResult(
        success=failed == 0,
        total=len(request.clip_ids),
        processed=processed,
        failed=failed,
        results=results,
        message=f"Deleted {processed} of {len(request.clip_ids)} clips"
    )


@router.post("/clips/bulk-apply-style", response_model=BulkOperationResult)
async def bulk_apply_style(
    request: BulkApplyStyleRequest,
    db: Session = Depends(get_db)
):
    """
    Apply subtitle style to multiple clips at once.
    Regenerates .ass files with the new style.
    """
    results = []
    processed = 0
    failed = 0

    style = {
        'font_name': request.subtitle_style.font_name,
        'font_size': request.subtitle_style.font_size,
        'primary_color': request.subtitle_style.primary_color,
        'outline_color': request.subtitle_style.outline_color,
        'outline': request.subtitle_style.outline_size,
        'shadow': request.subtitle_style.shadow_size,
        'margin_v': request.subtitle_style.margin_v,
    }

    for clip_id in request.clip_ids:
        try:
            clip = db.query(Clip).filter(Clip.id == clip_id).first()
            if not clip:
                results.append({
                    "clip_id": clip_id,
                    "success": False,
                    "error": "Clip not found"
                })
                failed += 1
                continue

            # Get subtitle data
            subtitle_data = clip.subtitle_data
            if isinstance(subtitle_data, str):
                subtitle_data = json.loads(subtitle_data)

            if not subtitle_data:
                results.append({
                    "clip_id": clip_id,
                    "success": False,
                    "error": "No subtitle data"
                })
                failed += 1
                continue

            # Extract words
            all_words = []
            for entry in subtitle_data:
                words = entry.get('words', [])
                if words:
                    all_words.extend(words)
                else:
                    text = entry.get('text', '')
                    start = entry.get('start', 0)
                    end = entry.get('end', 0)
                    word_list = text.split()
                    if word_list:
                        duration_per_word = (end - start) / len(word_list)
                        for j, word in enumerate(word_list):
                            all_words.append({
                                'word': word,
                                'start': start + j * duration_per_word,
                                'end': start + (j + 1) * duration_per_word
                            })

            # Generate new ASS file
            output_name = f"clip_{clip_id}"
            ass_path = CLIPS_DIR / f"{output_name}.ass"

            karaoke_enabled = request.subtitle_style.karaoke_enabled if request.subtitle_style else False

            if karaoke_enabled:
                subtitler.generate_ass_karaoke(
                    words=all_words,
                    output_path=str(ass_path),
                    offset=0,
                    style=style
                )
            else:
                subtitler.generate_ass(
                    words=all_words,
                    output_path=str(ass_path),
                    offset=0,
                    style=style
                )

            clip.subtitle_file = str(ass_path)
            clip.subtitle_path = str(ass_path)
            db.commit()

            results.append({
                "clip_id": clip_id,
                "success": True,
                "subtitle_file": str(ass_path)
            })
            processed += 1

        except Exception as e:
            db.rollback()
            results.append({
                "clip_id": clip_id,
                "success": False,
                "error": str(e)
            })
            failed += 1

    return BulkOperationResult(
        success=failed == 0,
        total=len(request.clip_ids),
        processed=processed,
        failed=failed,
        results=results,
        message=f"Applied style to {processed} of {len(request.clip_ids)} clips"
    )
