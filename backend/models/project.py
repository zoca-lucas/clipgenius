"""
ClipGenius - Project Model
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Enum
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
    youtube_url = Column(String(500), nullable=False)
    youtube_id = Column(String(50), nullable=False, unique=True)
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

    # Relationship
    clips = relationship("Clip", back_populates="project", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Project {self.id}: {self.title}>"
