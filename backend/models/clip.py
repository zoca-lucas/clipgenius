"""
ClipGenius - Clip Model
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Float, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from .database import Base


class Clip(Base):
    __tablename__ = "clips"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)

    # Timing
    start_time = Column(Float, nullable=False)  # seconds
    end_time = Column(Float, nullable=False)  # seconds
    duration = Column(Float)  # seconds

    # Metadata
    title = Column(String(200))
    viral_score = Column(Float)  # 0-10
    score_justification = Column(Text)
    categoria = Column(String(50))  # humor, insight, polêmica, emoção, dica

    # Files
    video_path = Column(String(500))
    video_path_with_subtitles = Column(String(500))
    subtitle_path = Column(String(500))  # .srt or .ass file

    # Subtitle layer system (for editor)
    subtitle_data = Column(JSON)  # Structured subtitle data: [{start, end, text, words}]
    subtitle_file = Column(String(500))  # Path to .ass subtitle file
    has_burned_subtitles = Column(Boolean, default=False)  # Whether subtitles are burned into video

    # Transcription segment
    transcription_segment = Column(Text)  # JSON string

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    project = relationship("Project", back_populates="clips")

    def __repr__(self):
        return f"<Clip {self.id}: {self.title} ({self.viral_score}/10)>"

    @property
    def formatted_duration(self) -> str:
        """Return duration as MM:SS format"""
        if not self.duration:
            return "0:00"
        minutes = int(self.duration // 60)
        seconds = int(self.duration % 60)
        return f"{minutes}:{seconds:02d}"
