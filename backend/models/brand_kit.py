"""
ClipGenius - Brand Kit Model
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean, Float
from sqlalchemy.orm import relationship
from .database import Base


class BrandKit(Base):
    __tablename__ = "brand_kits"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

    # Brand name
    brand_name = Column(String(255), nullable=True)

    # Logo/Watermark
    logo_path = Column(String(500), nullable=True)
    logo_position = Column(String(50), default="bottom-right")  # top-left, top-right, bottom-left, bottom-right, center
    logo_opacity = Column(Integer, default=80)  # 0-100
    logo_size = Column(Integer, default=15)  # % of video width

    # Colors
    primary_color = Column(String(20), default="#6366f1")  # Indigo
    secondary_color = Column(String(20), default="#8b5cf6")  # Purple
    text_color = Column(String(20), default="#ffffff")
    background_color = Column(String(20), default="#000000")

    # Subtitle styling
    subtitle_font = Column(String(100), default="Arial")
    subtitle_font_size = Column(Integer, default=48)
    subtitle_font_color = Column(String(20), default="#ffffff")
    subtitle_background = Column(Boolean, default=True)
    subtitle_background_color = Column(String(20), default="#000000")
    subtitle_background_opacity = Column(Integer, default=70)
    subtitle_position = Column(String(50), default="bottom")  # top, center, bottom

    # Intro/Outro
    intro_video_path = Column(String(500), nullable=True)
    intro_duration = Column(Float, default=0)  # seconds
    outro_video_path = Column(String(500), nullable=True)
    outro_duration = Column(Float, default=0)  # seconds

    # Custom font
    custom_font_path = Column(String(500), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    user = relationship("User", back_populates="brand_kit")

    def __repr__(self):
        return f"<BrandKit {self.id}: {self.brand_name or 'Unnamed'} for user {self.user_id}>"

    def to_dict(self) -> dict:
        """Convert to dictionary for FFmpeg processing"""
        return {
            "brand_name": self.brand_name,
            "logo": {
                "path": self.logo_path,
                "position": self.logo_position,
                "opacity": self.logo_opacity,
                "size": self.logo_size,
            },
            "colors": {
                "primary": self.primary_color,
                "secondary": self.secondary_color,
                "text": self.text_color,
                "background": self.background_color,
            },
            "subtitles": {
                "font": self.custom_font_path or self.subtitle_font,
                "font_size": self.subtitle_font_size,
                "font_color": self.subtitle_font_color,
                "background": self.subtitle_background,
                "background_color": self.subtitle_background_color,
                "background_opacity": self.subtitle_background_opacity,
                "position": self.subtitle_position,
            },
            "intro": {
                "path": self.intro_video_path,
                "duration": self.intro_duration,
            },
            "outro": {
                "path": self.outro_video_path,
                "duration": self.outro_duration,
            },
        }
