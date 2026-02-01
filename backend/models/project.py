"""
ClipGenius - Project Model
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
import enum
from .database import Base


class ProjectStatus(str, enum.Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    TRANSCRIBING = "transcribing"
    ANALYZING = "analyzing"
    CUTTING = "cutting"
    COMPLETED = "completed"
    ERROR = "error"


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)

    # User relationship (nullable for backward compatibility)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)

    youtube_url = Column(String(500), nullable=False)
    youtube_id = Column(String(50), nullable=False, index=True)  # Removed unique for multi-user support
    title = Column(String(500))
    duration = Column(Integer)  # seconds
    thumbnail_url = Column(String(500))
    video_path = Column(String(500))
    audio_path = Column(String(500))
    transcription = Column(Text)  # JSON string
    status = Column(String(50), default=ProjectStatus.PENDING.value)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Progress tracking
    progress = Column(Integer, default=0)  # 0-100%
    progress_message = Column(String(500))  # Detailed message
    progress_step = Column(String(100))  # e.g., "8/15"
    progress_started_at = Column(DateTime)  # For ETA calculation

    # Processing lock to prevent concurrent processing
    is_processing = Column(Boolean, default=False)
    processing_started_at = Column(DateTime)

    # Relationships
    user = relationship("User", back_populates="projects")
    clips = relationship("Clip", back_populates="project", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Project {self.id}: {self.title}>"

    def acquire_processing_lock(self) -> bool:
        """
        Try to acquire processing lock.
        Returns True if lock acquired, False if already processing.
        """
        if self.is_processing:
            # Check if processing is stale (> 10 minutes)
            if self.processing_started_at:
                elapsed = (datetime.utcnow() - self.processing_started_at).total_seconds()
                if elapsed > 600:  # 10 minutes
                    # Stale lock, can be overridden
                    self.is_processing = True
                    self.processing_started_at = datetime.utcnow()
                    return True
            return False

        self.is_processing = True
        self.processing_started_at = datetime.utcnow()
        return True

    def release_processing_lock(self):
        """Release the processing lock"""
        self.is_processing = False
        self.processing_started_at = None
