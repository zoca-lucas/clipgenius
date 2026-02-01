"""
ClipGenius - User Model
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float
from sqlalchemy.orm import relationship
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(255), nullable=True)

    # Credits system
    credits = Column(Integer, default=60)  # Free tier starts with 60 credits
    is_premium = Column(Boolean, default=False)

    # Account status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime, nullable=True)

    # Gamification
    streak_days = Column(Integer, default=0)
    last_checkin_at = Column(DateTime, nullable=True)
    total_clips_generated = Column(Integer, default=0)
    total_videos_processed = Column(Integer, default=0)

    # Relationships
    projects = relationship("Project", back_populates="user", cascade="all, delete-orphan")
    credit_transactions = relationship("CreditTransaction", back_populates="user", cascade="all, delete-orphan")
    subscription = relationship("Subscription", back_populates="user", uselist=False, cascade="all, delete-orphan")
    brand_kit = relationship("BrandKit", back_populates="user", uselist=False, cascade="all, delete-orphan")
    social_accounts = relationship("SocialAccount", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.id}: {self.email}>"

    def has_credits(self, amount: int) -> bool:
        """Check if user has enough credits"""
        return self.credits >= amount

    def deduct_credits(self, amount: int) -> bool:
        """Deduct credits from user. Returns True if successful."""
        if self.credits >= amount:
            self.credits -= amount
            return True
        return False

    def add_credits(self, amount: int):
        """Add credits to user"""
        self.credits += amount
