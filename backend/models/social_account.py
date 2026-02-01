"""
ClipGenius - Social Account Model
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
import enum
from .database import Base


class SocialPlatform(str, enum.Enum):
    TIKTOK = "tiktok"
    INSTAGRAM = "instagram"
    YOUTUBE = "youtube"
    TWITTER = "twitter"
    FACEBOOK = "facebook"
    LINKEDIN = "linkedin"


class SocialAccount(Base):
    __tablename__ = "social_accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Platform info
    platform = Column(String(50), nullable=False)
    platform_user_id = Column(String(255), nullable=True)
    platform_username = Column(String(255), nullable=True)
    platform_display_name = Column(String(255), nullable=True)
    platform_profile_url = Column(String(500), nullable=True)
    platform_avatar_url = Column(String(500), nullable=True)

    # OAuth tokens (encrypted in production)
    access_token = Column(Text, nullable=True)
    refresh_token = Column(Text, nullable=True)
    token_expires_at = Column(DateTime, nullable=True)

    # Account status
    is_connected = Column(Boolean, default=True)
    last_error = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)

    # Relationship
    user = relationship("User", back_populates="social_accounts")

    def __repr__(self):
        return f"<SocialAccount {self.id}: {self.platform} - {self.platform_username}>"

    @property
    def is_token_valid(self) -> bool:
        """Check if token is still valid"""
        if not self.access_token:
            return False
        if self.token_expires_at and datetime.utcnow() > self.token_expires_at:
            return False
        return True

    @property
    def needs_refresh(self) -> bool:
        """Check if token needs refresh (expires in < 1 hour)"""
        if not self.token_expires_at:
            return False
        from datetime import timedelta
        return datetime.utcnow() > (self.token_expires_at - timedelta(hours=1))


class ScheduledPost(Base):
    """Scheduled posts for social media"""
    __tablename__ = "scheduled_posts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    social_account_id = Column(Integer, ForeignKey("social_accounts.id"), nullable=False)
    clip_id = Column(Integer, ForeignKey("clips.id"), nullable=False)

    # Post content
    caption = Column(Text, nullable=True)
    hashtags = Column(Text, nullable=True)

    # Scheduling
    scheduled_at = Column(DateTime, nullable=False)
    posted_at = Column(DateTime, nullable=True)

    # Status
    status = Column(String(50), default="scheduled")  # scheduled, posting, posted, failed
    platform_post_id = Column(String(255), nullable=True)
    error_message = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<ScheduledPost {self.id}: clip {self.clip_id} at {self.scheduled_at}>"
