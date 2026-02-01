"""
ClipGenius - API Routes
"""
import json
import uuid
import shutil
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pathlib import Path

from config import VIDEOS_DIR, MAX_UPLOAD_SIZE, ALLOWED_VIDEO_EXTENSIONS, ALLOWED_MIME_TYPES

from models import get_db, Project, Clip, SessionLocal
from models.project import ProjectStatus
from services import (
    YouTubeDownloader,
    WhisperTranscriber,
    ClipAnalyzer,
    VideoCutter,
    SubtitleGenerator
)
from .schemas import (
    ProjectCreate,
    ProjectResponse,
    ProjectDetailResponse,
    ProjectListResponse,
    ClipResponse,
    ClipListResponse,
    ClipRegenerate,
    ProcessingStatus
)

router = APIRouter()

# Initialize services
downloader = YouTubeDownloader()
transcriber = WhisperTranscriber()
cutter = VideoCutter()
subtitler = SubtitleGenerator()


def get_analyzer():
    """Lazy load analyzer (requires API key)"""
    return ClipAnalyzer()


# ============ Background Processing ============

def process_video(project_id: int):
    """
    Background task to process video:
    1. Download video
    2. Transcribe audio
    3. Analyze with AI
    4. Cut clips
    5. Add subtitles

    IMPORTANTE: Cria sua própria sessão SQLAlchemy para não depender do escopo da requisição HTTP.
    """
    db = SessionLocal()
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            db.close()
            return

        try:
            # Step 1: Download (skip if video already exists - upload case)
            if project.video_path and Path(project.video_path).exists():
                print(f"📁 Video already exists, skipping download: {project.video_path}")
            else:
                project.status = ProjectStatus.DOWNLOADING.value
                db.commit()

                video_info = downloader.download(project.youtube_url, project.youtube_id)
                project.title = video_info['title']
                project.duration = video_info['duration']
                project.thumbnail_url = video_info['thumbnail']
                project.video_path = video_info['video_path']
                db.commit()

            # Step 2: Transcribe
            project.status = ProjectStatus.TRANSCRIBING.value
            db.commit()

            transcription = transcriber.transcribe_video(project.video_path)
            project.audio_path = transcription.get('audio_path')
            project.transcription = json.dumps(transcription)
            db.commit()

            # Step 3: Analyze with AI
            project.status = ProjectStatus.ANALYZING.value
            db.commit()

            analyzer = get_analyzer()
            clip_suggestions = analyzer.analyze(transcription)

            # Step 4 & 5: Cut clips and add subtitles
            project.status = ProjectStatus.CUTTING.value
            db.commit()

            for i, suggestion in enumerate(clip_suggestions):
                # Cut the clip
                clip_name = f"{project.youtube_id}_clip_{i+1:02d}"

                clip_result = cutter.cut_clip(
                    video_path=project.video_path,
                    start_time=suggestion['start_time'],
                    end_time=suggestion['end_time'],
                    output_name=clip_name,
                    convert_to_vertical=True
                )

                # Get transcription segment for this clip
                segment = transcriber.get_text_for_timerange(
                    transcription,
                    suggestion['start_time'],
                    suggestion['end_time']
                )

                # Add subtitles
                words = segment.get('words', [])
                if words:
                    subtitle_result = subtitler.create_subtitled_clip(
                        video_path=clip_result['video_path'],
                        words=words,
                        clip_start_time=suggestion['start_time'],
                        output_name=clip_name
                    )
                else:
                    subtitle_result = {}

                # Create clip record
                clip = Clip(
                    project_id=project.id,
                    start_time=suggestion['start_time'],
                    end_time=suggestion['end_time'],
                    duration=suggestion['duration'],
                    title=suggestion['title'],
                    viral_score=suggestion['viral_score'],
                    score_justification=suggestion['justification'],
                    video_path=clip_result['video_path'],
                    video_path_with_subtitles=subtitle_result.get('video_path_with_subtitles'),
                    subtitle_path=subtitle_result.get('subtitle_path'),
                    transcription_segment=json.dumps(segment)
                )
                db.add(clip)
                db.commit()

            # Done!
            project.status = ProjectStatus.COMPLETED.value
            db.commit()

        except Exception as e:
            project.status = ProjectStatus.ERROR.value
            project.error_message = str(e)
            db.commit()
            raise
    finally:
        db.close()


# ============ Project Endpoints ============

@router.post("/projects", response_model=ProjectResponse)
async def create_project(
    project_data: ProjectCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Create a new project from YouTube URL"""
    # Validate URL
    if not downloader.validate_url(project_data.url):
        raise HTTPException(status_code=400, detail="Invalid YouTube URL")

    # Extract video ID
    video_id = downloader.extract_video_id(project_data.url)

    # Check if project already exists
    existing = db.query(Project).filter(Project.youtube_id == video_id).first()
    if existing:
        return ProjectResponse(
            id=existing.id,
            youtube_url=existing.youtube_url,
            youtube_id=existing.youtube_id,
            title=existing.title,
            duration=existing.duration,
            thumbnail_url=existing.thumbnail_url,
            status=existing.status,
            error_message=existing.error_message,
            created_at=existing.created_at,
            updated_at=existing.updated_at,
            clips_count=len(existing.clips)
        )

    # Get video info
    try:
        video_info = downloader.get_video_info(project_data.url)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not fetch video info: {str(e)}")

    # Create project
    project = Project(
        youtube_url=project_data.url,
        youtube_id=video_id,
        title=video_info.get('title'),
        duration=video_info.get('duration'),
        thumbnail_url=video_info.get('thumbnail'),
        status=ProjectStatus.PENDING.value
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    # Start background processing
    background_tasks.add_task(process_video, project.id)

    return ProjectResponse(
        id=project.id,
        youtube_url=project.youtube_url,
        youtube_id=project.youtube_id,
        title=project.title,
        duration=project.duration,
        thumbnail_url=project.thumbnail_url,
        status=project.status,
        error_message=project.error_message,
        created_at=project.created_at,
        updated_at=project.updated_at,
        clips_count=0
    )


@router.post("/projects/upload", response_model=ProjectResponse)
async def upload_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload a local video file (MP4, MOV, AVI, MKV, WebM)
    Max size: 500MB
    """
    # Validate file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_VIDEO_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_VIDEO_EXTENSIONS)}"
        )

    # Validate MIME type
    if file.content_type and file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid content type: {file.content_type}"
        )

    # Generate unique ID for the file
    file_id = str(uuid.uuid4())[:12]

    # Get filename without extension for title
    original_name = Path(file.filename).stem

    # Save file
    output_path = VIDEOS_DIR / f"{file_id}.mp4"

    try:
        # Check file size while saving
        total_size = 0
        with open(output_path, "wb") as buffer:
            while chunk := file.file.read(1024 * 1024):  # 1MB chunks
                total_size += len(chunk)
                if total_size > MAX_UPLOAD_SIZE:
                    buffer.close()
                    output_path.unlink()  # Delete partial file
                    raise HTTPException(
                        status_code=413,
                        detail=f"File too large. Max size: {MAX_UPLOAD_SIZE // (1024*1024)}MB"
                    )
                buffer.write(chunk)
    except HTTPException:
        raise
    except Exception as e:
        if output_path.exists():
            output_path.unlink()
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    # Get video duration using ffprobe
    duration = None
    try:
        import subprocess
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
             '-of', 'default=noprint_wrappers=1:nokey=1', str(output_path)],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            duration = int(float(result.stdout.strip()))
    except Exception:
        pass  # Duration is optional

    # Create project
    project = Project(
        youtube_url=f"upload://{file.filename}",  # Mark as upload
        youtube_id=file_id,
        title=original_name,
        duration=duration,
        thumbnail_url=None,  # No thumbnail for uploads
        video_path=str(output_path),
        status=ProjectStatus.DOWNLOADING.value  # Skip download step
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    # Start background processing (will skip download since video_path exists)
    background_tasks.add_task(process_video, project.id)

    return ProjectResponse(
        id=project.id,
        youtube_url=project.youtube_url,
        youtube_id=project.youtube_id,
        title=project.title,
        duration=project.duration,
        thumbnail_url=project.thumbnail_url,
        status=project.status,
        error_message=project.error_message,
        created_at=project.created_at,
        updated_at=project.updated_at,
        clips_count=0
    )


@router.get("/projects", response_model=ProjectListResponse)
async def list_projects(
    page: int = 1,
    per_page: int = 10,
    db: Session = Depends(get_db)
):
    """List all projects"""
    offset = (page - 1) * per_page
    total = db.query(Project).count()
    projects = db.query(Project).order_by(Project.created_at.desc()).offset(offset).limit(per_page).all()

    items = [
        ProjectResponse(
            id=p.id,
            youtube_url=p.youtube_url,
            youtube_id=p.youtube_id,
            title=p.title,
            duration=p.duration,
            thumbnail_url=p.thumbnail_url,
            status=p.status,
            error_message=p.error_message,
            created_at=p.created_at,
            updated_at=p.updated_at,
            clips_count=len(p.clips)
        )
        for p in projects
    ]

    return ProjectListResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page
    )


@router.get("/projects/{project_id}", response_model=ProjectDetailResponse)
async def get_project(project_id: int, db: Session = Depends(get_db)):
    """Get project details with clips"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    clips = [ClipResponse.model_validate(c) for c in project.clips]

    return ProjectDetailResponse(
        id=project.id,
        youtube_url=project.youtube_url,
        youtube_id=project.youtube_id,
        title=project.title,
        duration=project.duration,
        thumbnail_url=project.thumbnail_url,
        status=project.status,
        error_message=project.error_message,
        created_at=project.created_at,
        updated_at=project.updated_at,
        clips_count=len(clips),
        clips=clips
    )


@router.delete("/projects/{project_id}")
async def delete_project(project_id: int, db: Session = Depends(get_db)):
    """Delete a project and all its clips"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    db.delete(project)
    db.commit()

    return {"message": "Project deleted successfully"}


@router.get("/projects/{project_id}/status", response_model=ProcessingStatus)
async def get_project_status(project_id: int, db: Session = Depends(get_db)):
    """Get current processing status of a project"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    status_messages = {
        ProjectStatus.PENDING.value: "Aguardando processamento...",
        ProjectStatus.DOWNLOADING.value: "Baixando vídeo do YouTube...",
        ProjectStatus.TRANSCRIBING.value: "Transcrevendo áudio com Whisper...",
        ProjectStatus.ANALYZING.value: "Analisando conteúdo com IA...",
        ProjectStatus.CUTTING.value: "Gerando cortes e legendas...",
        ProjectStatus.COMPLETED.value: "Processamento concluído!",
        ProjectStatus.ERROR.value: f"Erro: {project.error_message}",
    }

    return ProcessingStatus(
        project_id=project.id,
        status=project.status,
        current_step=project.status,
        message=status_messages.get(project.status, "Processando...")
    )


@router.post("/projects/{project_id}/reprocess", response_model=ProjectResponse)
async def reprocess_project(
    project_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Reprocess a project that failed or needs to be regenerated.
    Only projects with 'error' or 'completed' status can be reprocessed.
    """
    from datetime import datetime

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Only allow reprocessing for error or completed status
    if project.status not in [ProjectStatus.ERROR.value, ProjectStatus.COMPLETED.value]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot reprocess project with status '{project.status}'. Only 'error' or 'completed' projects can be reprocessed."
        )

    # Delete existing clips if reprocessing completed project
    if project.status == ProjectStatus.COMPLETED.value:
        for clip in project.clips:
            # Delete clip files
            for path in [clip.video_path, clip.video_path_with_subtitles, clip.subtitle_path]:
                if path and Path(path).exists():
                    try:
                        Path(path).unlink()
                    except Exception as e:
                        print(f"⚠️  Could not delete file {path}: {e}")
            db.delete(clip)
        db.commit()

    # Reset project status
    project.status = ProjectStatus.PENDING.value
    project.error_message = None
    project.updated_at = datetime.utcnow()

    # If video was already downloaded, start from transcription
    if project.video_path and Path(project.video_path).exists():
        project.status = ProjectStatus.DOWNLOADING.value  # Will skip download

    db.commit()
    db.refresh(project)

    # Start background processing
    background_tasks.add_task(process_video, project.id)

    return ProjectResponse(
        id=project.id,
        youtube_url=project.youtube_url,
        youtube_id=project.youtube_id,
        title=project.title,
        duration=project.duration,
        thumbnail_url=project.thumbnail_url,
        status=project.status,
        error_message=project.error_message,
        created_at=project.created_at,
        updated_at=project.updated_at,
        clips_count=len(project.clips)
    )


# ============ Clip Endpoints ============

@router.get("/projects/{project_id}/clips", response_model=ClipListResponse)
async def list_clips(project_id: int, db: Session = Depends(get_db)):
    """List all clips for a project"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    clips = db.query(Clip).filter(Clip.project_id == project_id).order_by(Clip.viral_score.desc()).all()

    return ClipListResponse(
        items=[ClipResponse.model_validate(c) for c in clips],
        total=len(clips)
    )


@router.get("/clips/{clip_id}", response_model=ClipResponse)
async def get_clip(clip_id: int, db: Session = Depends(get_db)):
    """Get clip details"""
    clip = db.query(Clip).filter(Clip.id == clip_id).first()
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")

    return ClipResponse.model_validate(clip)


@router.get("/clips/{clip_id}/download")
async def download_clip(
    clip_id: int,
    with_subtitles: bool = True,
    db: Session = Depends(get_db)
):
    """Download a clip video file"""
    clip = db.query(Clip).filter(Clip.id == clip_id).first()
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")

    # Choose video path based on preference
    if with_subtitles and clip.video_path_with_subtitles:
        video_path = clip.video_path_with_subtitles
    else:
        video_path = clip.video_path

    if not video_path or not Path(video_path).exists():
        raise HTTPException(status_code=404, detail="Video file not found")

    filename = f"{clip.title or f'clip_{clip.id}'}.mp4"

    return FileResponse(
        video_path,
        media_type="video/mp4",
        filename=filename
    )


@router.delete("/clips/{clip_id}")
async def delete_clip(clip_id: int, db: Session = Depends(get_db)):
    """Delete a clip"""
    clip = db.query(Clip).filter(Clip.id == clip_id).first()
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")

    # Optionally delete files
    for path in [clip.video_path, clip.video_path_with_subtitles, clip.subtitle_path]:
        if path and Path(path).exists():
            Path(path).unlink()

    db.delete(clip)
    db.commit()

    return {"message": "Clip deleted successfully"}
