"""
ClipGenius - API Routes
"""
import json
import subprocess
import uuid
import shutil
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pathlib import Path

from config import (
    VIDEOS_DIR,
    MAX_UPLOAD_SIZE,
    ALLOWED_VIDEO_EXTENSIONS,
    ALLOWED_MIME_TYPES,
    ENABLE_AI_REFRAME,
    REFRAME_SAMPLE_INTERVAL,
    REFRAME_DYNAMIC_MODE,
    NUM_CLIPS_TO_GENERATE,
    OUTPUT_FORMATS,
    DEFAULT_OUTPUT_FORMAT
)

from models import get_db, Project, Clip, get_background_session, db_lock
from models.project import ProjectStatus
from services import (
    YouTubeDownloader,
    WhisperTranscriber,
    ClipAnalyzer,
    VideoCutter,
    SubtitleGenerator,
    AIReframer
)
from .schemas import (
    ProjectCreate,
    ProjectResponse,
    ProjectDetailResponse,
    ProjectListResponse,
    ClipResponse,
    ClipListResponse,
    ClipRegenerate,
    ProcessingStatus,
    OutputFormat,
    OutputFormatsResponse,
    ClipExportRequest
)

router = APIRouter()

# Initialize services
downloader = YouTubeDownloader()
transcriber = WhisperTranscriber()
cutter = VideoCutter()
subtitler = SubtitleGenerator()
reframer = AIReframer()


def get_analyzer():
    """Lazy load analyzer (requires API key)"""
    return ClipAnalyzer()


# Progress tracking weights for each step (must sum to 100)
STEP_WEIGHTS = {
    'downloading': 15,    # 0-15%
    'transcribing': 25,   # 15-40%
    'analyzing': 20,      # 40-60%
    'cutting': 40,        # 60-100%
}

STEP_BASE_PROGRESS = {
    'downloading': 0,
    'transcribing': 15,
    'analyzing': 40,
    'cutting': 60,
}


def update_progress(
    db: Session,
    project: Project,
    status: str,
    progress: int,
    message: str,
    step_progress: str = None
):
    """
    Update project progress in database with error handling.

    Args:
        db: Database session
        project: Project to update
        status: Current status (downloading, transcribing, etc.)
        progress: Overall progress 0-100%
        message: Human-readable message
        step_progress: Optional step progress like "8/15"
    """
    try:
        project.status = status
        project.progress = min(100, max(0, progress))
        project.progress_message = message
        project.progress_step = step_progress

        # Set start time on first progress update
        if project.progress_started_at is None:
            project.progress_started_at = datetime.utcnow()

        db.commit()
    except Exception as e:
        print(f"⚠️ Failed to update progress: {e}")
        db.rollback()
        raise


def cut_clip_with_optional_reframe(
    video_path: str,
    start_time: float,
    end_time: float,
    output_name: str,
    enable_reframe: bool = ENABLE_AI_REFRAME
) -> dict:
    """
    Cut a clip with optional AI reframing (face tracking).
    Falls back to center crop if reframe is disabled or fails.
    """
    if enable_reframe:
        try:
            if REFRAME_DYNAMIC_MODE:
                # Frame-by-frame tracking (slower but smoother)
                return reframer.cut_clip_with_dynamic_tracking(
                    video_path=video_path,
                    start_time=start_time,
                    end_time=end_time,
                    output_name=output_name,
                    sample_interval=REFRAME_SAMPLE_INTERVAL
                )
            else:
                # Static tracking (faster, uses average face position)
                return reframer.cut_clip_with_tracking(
                    video_path=video_path,
                    start_time=start_time,
                    end_time=end_time,
                    output_name=output_name,
                    enable_tracking=True,
                    sample_interval=REFRAME_SAMPLE_INTERVAL
                )
        except Exception as e:
            print(f"⚠️  AI Reframe failed, falling back to center crop: {e}")

    # Fallback to simple center crop
    return cutter.cut_clip(
        video_path=video_path,
        start_time=start_time,
        end_time=end_time,
        output_name=output_name,
        convert_to_vertical=True
    )


# ============ Background Processing ============

def process_video(project_id: int):
    """
    Background task to process video with progress tracking:
    1. Download video (0-15%)
    2. Transcribe audio (15-40%)
    3. Analyze with AI (40-60%)
    4. Cut clips + subtitles (60-100%)

    Uses thread-safe database session and processing lock to prevent race conditions.
    """
    db = get_background_session()
    project = None

    try:
        # Acquire lock and fetch project atomically
        with db_lock:
            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                print(f"⚠️ Project {project_id} not found")
                return

            # Try to acquire processing lock
            if not project.acquire_processing_lock():
                print(f"⚠️ Project {project_id} is already being processed")
                db.rollback()
                return

            # Initialize progress tracking
            project.progress_started_at = datetime.utcnow()
            db.commit()

        # ========== Step 1: Download (0-15%) ==========
        if project.video_path and Path(project.video_path).exists():
            print(f"📁 Video already exists, skipping download: {project.video_path}")
            update_progress(db, project, ProjectStatus.DOWNLOADING.value, 15,
                           "Vídeo já existe, pulando download...")
        else:
            # Detect source from URL
            source = detect_url_source(project.youtube_url)

            if source == "google_drive":
                update_progress(db, project, ProjectStatus.DOWNLOADING.value, 0,
                               "Iniciando download do Google Drive...")

                update_progress(db, project, ProjectStatus.DOWNLOADING.value, 5,
                               "Conectando ao Google Drive...")

                video_info = google_drive_downloader.download(
                    project.youtube_url,
                    project.youtube_id
                )
                project.title = video_info.get('title') or project.title
                project.video_path = video_info['video_path']
                # Duration and thumbnail not available from Google Drive
            else:
                # Default to YouTube
                update_progress(db, project, ProjectStatus.DOWNLOADING.value, 0,
                               "Iniciando download do YouTube...")

                update_progress(db, project, ProjectStatus.DOWNLOADING.value, 5,
                               "Conectando ao YouTube...")

                video_info = downloader.download(project.youtube_url, project.youtube_id)
                project.title = video_info['title']
                project.duration = video_info['duration']
                project.thumbnail_url = video_info['thumbnail']
                project.video_path = video_info['video_path']

            update_progress(db, project, ProjectStatus.DOWNLOADING.value, 15,
                           "Download concluído!")

        # ========== Step 2: Transcribe (15-40%) ==========
        update_progress(db, project, ProjectStatus.TRANSCRIBING.value, 16,
                       "Extraindo áudio do vídeo...")

        update_progress(db, project, ProjectStatus.TRANSCRIBING.value, 20,
                       "Transcrevendo com Whisper AI...")

        transcription = transcriber.transcribe_video(project.video_path)
        project.audio_path = transcription.get('audio_path')
        project.transcription = json.dumps(transcription)

        update_progress(db, project, ProjectStatus.TRANSCRIBING.value, 40,
                       "Transcrição concluída!")

        # ========== Step 3: Analyze with AI (40-60%) ==========
        update_progress(db, project, ProjectStatus.ANALYZING.value, 41,
                       "Enviando para análise de IA...")

        update_progress(db, project, ProjectStatus.ANALYZING.value, 45,
                       "IA identificando momentos virais...")

        analyzer = get_analyzer()
        clip_suggestions = analyzer.analyze(transcription)

        update_progress(db, project, ProjectStatus.ANALYZING.value, 60,
                       f"IA encontrou {len(clip_suggestions)} momentos virais!")

        # ========== Step 4 & 5: Cut clips + subtitles (60-100%) ==========
        total_clips = len(clip_suggestions)
        clip_progress_weight = 40  # 40% do progresso total (60-100)

        for i, suggestion in enumerate(clip_suggestions):
            clip_num = i + 1

            # Calculate progress within cutting phase
            clip_progress = int(60 + (clip_progress_weight * clip_num / total_clips))

            reframe_text = " com AI Reframe" if ENABLE_AI_REFRAME else ""
            update_progress(
                db, project,
                ProjectStatus.CUTTING.value,
                clip_progress - 2,  # Slightly before completion
                f"Gerando corte {clip_num}/{total_clips}{reframe_text}...",
                f"{clip_num}/{total_clips}"
            )

            # Cut the clip with AI reframe (face tracking)
            clip_name = f"{project.youtube_id}_clip_{clip_num:02d}"

            clip_result = cut_clip_with_optional_reframe(
                video_path=project.video_path,
                start_time=suggestion['start_time'],
                end_time=suggestion['end_time'],
                output_name=clip_name,
                enable_reframe=ENABLE_AI_REFRAME
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

            # Create clip record with atomic transaction
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
        update_progress(
            db, project,
            ProjectStatus.COMPLETED.value,
            100,
            f"Concluído! {total_clips} cortes gerados com sucesso.",
            f"{total_clips}/{total_clips}"
        )

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"❌ Error processing project {project_id}: {e}")
        print(f"   Traceback: {error_trace}")
        db.rollback()  # Rollback any pending changes

        # Create user-friendly error message
        error_str = str(e)
        if "ConnectionError" in error_str or "ConnectError" in error_str:
            user_message = "Erro de conexão. Verifique se o Ollama está rodando ou se a API Groq está acessível."
        elif "ffmpeg" in error_str.lower() or "ffprobe" in error_str.lower():
            user_message = "Erro no processamento de vídeo. Verifique se o FFmpeg está instalado."
        elif "whisper" in error_str.lower():
            user_message = "Erro na transcrição de áudio. Verifique a instalação do Whisper."
        elif "Private video" in error_str or "video unavailable" in error_str.lower():
            user_message = "Vídeo indisponível ou privado no YouTube."
        elif "copyright" in error_str.lower():
            user_message = "Vídeo bloqueado por direitos autorais."
        else:
            user_message = f"Erro no processamento: {error_str[:200]}"

        # Update project status to error
        try:
            if project:
                project.status = ProjectStatus.ERROR.value
                project.error_message = error_str[:500]  # Limit error message length
                project.progress_message = user_message
                db.commit()
        except Exception as commit_error:
            print(f"❌ Failed to update error status: {commit_error}")
            db.rollback()

    finally:
        # Always release processing lock and close session
        try:
            if project:
                project.release_processing_lock()
                db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()


# ============ Project Endpoints ============

def detect_url_source(url: str) -> str:
    """Detect if URL is YouTube, Google Drive, or unknown"""
    if downloader.validate_url(url):
        return "youtube"
    if google_drive_downloader.validate_url(url):
        return "google_drive"
    return "unknown"


@router.post("/projects", response_model=ProjectResponse)
async def create_project(
    project_data: ProjectCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Create a new project from YouTube or Google Drive URL"""
    url = project_data.url
    source = detect_url_source(url)

    if source == "unknown":
        raise HTTPException(
            status_code=400,
            detail="Invalid URL. Please provide a valid YouTube or Google Drive URL."
        )

    # Extract video ID based on source
    if source == "youtube":
        video_id = downloader.extract_video_id(url)
    else:  # google_drive
        video_id = google_drive_downloader.extract_file_id(url)

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

    # Get video info based on source
    try:
        if source == "youtube":
            video_info = downloader.get_video_info(url)
        else:  # google_drive
            video_info = google_drive_downloader.get_file_info(url)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not fetch video info: {str(e)}")

    # Create project
    project = Project(
        youtube_url=url,  # Store original URL regardless of source
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
    """Delete a project and all its clips, including files on disk"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Check if project is being processed
    if project.is_processing:
        raise HTTPException(
            status_code=409,
            detail="Cannot delete project while it's being processed. Please wait for processing to complete."
        )

    # Delete associated files
    files_to_delete = []

    # Video and audio files
    if project.video_path:
        files_to_delete.append(project.video_path)
    if project.audio_path:
        files_to_delete.append(project.audio_path)

    # Clip files
    for clip in project.clips:
        if clip.video_path:
            files_to_delete.append(clip.video_path)
        if clip.video_path_with_subtitles:
            files_to_delete.append(clip.video_path_with_subtitles)
        if clip.subtitle_path:
            files_to_delete.append(clip.subtitle_path)

    # Delete files (ignore errors)
    deleted_files = 0
    for file_path in files_to_delete:
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                deleted_files += 1
        except Exception as e:
            print(f"⚠️ Could not delete file {file_path}: {e}")

    # Delete from database (cascade will delete clips)
    db.delete(project)
    db.commit()

    return {
        "message": "Project deleted successfully",
        "files_deleted": deleted_files
    }


@router.get("/projects/{project_id}/status", response_model=ProcessingStatus)
async def get_project_status(project_id: int, db: Session = Depends(get_db)):
    """Get current processing status of a project with detailed progress"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Calculate ETA based on progress and elapsed time
    eta_seconds = None
    if project.progress_started_at and project.progress and project.progress > 0 and project.progress < 100:
        elapsed = (datetime.utcnow() - project.progress_started_at).total_seconds()
        # ETA = (elapsed / progress) * remaining_progress
        remaining_progress = 100 - project.progress
        eta_seconds = int((elapsed / project.progress) * remaining_progress)

    # Use custom message if available, otherwise use default
    reframe_status = " com AI Reframe" if ENABLE_AI_REFRAME else ""
    default_messages = {
        ProjectStatus.PENDING.value: "Aguardando processamento...",
        ProjectStatus.DOWNLOADING.value: "Baixando vídeo do YouTube...",
        ProjectStatus.TRANSCRIBING.value: "Transcrevendo áudio com Whisper...",
        ProjectStatus.ANALYZING.value: "Analisando conteúdo com IA...",
        ProjectStatus.CUTTING.value: f"Gerando cortes{reframe_status} e legendas...",
        ProjectStatus.COMPLETED.value: "Processamento concluído!",
        ProjectStatus.ERROR.value: f"Erro: {project.error_message}",
    }

    message = project.progress_message or default_messages.get(project.status, "Processando...")

    return ProcessingStatus(
        project_id=project.id,
        status=project.status,
        progress=project.progress or 0,
        current_step=project.status,
        step_progress=project.progress_step,
        eta_seconds=eta_seconds,
        message=message
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
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Check if project is already being processed
    if project.is_processing:
        raise HTTPException(
            status_code=409,
            detail="Project is already being processed. Please wait for processing to complete."
        )

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


# ============ Output Format Endpoints ============

@router.get("/formats", response_model=OutputFormatsResponse)
async def list_output_formats():
    """List all available output formats"""
    formats = [
        OutputFormat(
            id=fmt["id"],
            name=fmt["name"],
            aspect_ratio=fmt["aspect_ratio"],
            resolution=fmt["resolution"],
            platforms=fmt["platforms"],
            description=fmt["description"]
        )
        for fmt in OUTPUT_FORMATS.values()
    ]

    return OutputFormatsResponse(
        formats=formats,
        default=DEFAULT_OUTPUT_FORMAT
    )


@router.post("/clips/{clip_id}/export")
async def export_clip_format(
    clip_id: int,
    export_request: ClipExportRequest,
    db: Session = Depends(get_db)
):
    """
    Export a clip in a different format.
    Creates a new video file with the specified aspect ratio.
    """
    clip = db.query(Clip).filter(Clip.id == clip_id).first()
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")

    # Validate timestamps
    if clip.start_time >= clip.end_time:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid clip timestamps: start_time ({clip.start_time}) must be less than end_time ({clip.end_time})"
        )

    # Validate format
    format_id = export_request.format_id
    if format_id not in OUTPUT_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid format. Available: {', '.join(OUTPUT_FORMATS.keys())}"
        )

    # Get project to access original video
    project = clip.project
    if not project or not project.video_path:
        raise HTTPException(status_code=404, detail="Original video not found")

    # Generate new clip in requested format
    output_name = f"{project.youtube_id}_clip_{clip.id:02d}_{format_id}"

    try:
        result = cutter.cut_clip(
            video_path=project.video_path,
            start_time=clip.start_time,
            end_time=clip.end_time,
            output_name=output_name,
            output_format=format_id
        )

        # Return download URL
        fmt = OUTPUT_FORMATS[format_id]
        return {
            "message": f"Clip exported in {fmt['name']} format",
            "format": format_id,
            "resolution": fmt["resolution"],
            "platforms": fmt["platforms"],
            "video_path": result["video_path"],
            "download_url": f"/clips/export/{Path(result['video_path']).name}"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")
