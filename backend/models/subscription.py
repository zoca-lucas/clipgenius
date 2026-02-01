"""
ClipGenius - Subscription & Plan Models
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship
import enum
from .database import Base


class PlanType(str, enum.Enum):
    FREE = "free"
    LITE = "lite"
    CREATOR = "creator"
    VIRAL = "viral"


# Plan definitions
PLANS = {
    "free": {
        "id": "free",
        "name": "Grátis",
        "credits": 60,
        "price": 0,
        "price_yearly": 0,
        "features": [
            "60 créditos/mês",
            "15 cortes por vídeo",
            "Legendas automáticas",
            "Download em 720p",
        ],
        "limits": {
            "max_video_duration": 1800,  # 30 minutes
            "max_clips_per_video": 15,
            "max_projects": 10,
        }
    },
    "lite": {
        "id": "lite",
        "name": "Lite",
        "credits": 180,
        "price": 14.95,
        "price_yearly": 119.95,
        "features": [
            "180 créditos/mês",
            "15 cortes por vídeo",
            "Legendas automáticas",
            "Download em 1080p",
            "AI Reframe (face tracking)",
            "Brand Kit básico",
        ],
        "limits": {
            "max_video_duration": 3600,  # 1 hour
            "max_clips_per_video": 15,
            "max_projects": 50,
        }
    },
    "creator": {
        "id": "creator",
        "name": "Creator",
        "credits": 420,
        "price": 44.95,
        "price_yearly": 359.95,
        "features": [
            "420 créditos/mês",
            "15 cortes por vídeo",
            "Legendas personalizadas",
            "Download em 1080p",
            "AI Reframe (face tracking)",
            "Brand Kit completo",
            "Publicação em redes sociais",
            "Suporte prioritário",
        ],
        "limits": {
            "max_video_duration": 7200,  # 2 hours
            "max_clips_per_video": 15,
            "max_projects": 200,
        }
    },
    "viral": {
        "id": "viral",
        "name": "Viral",
        "credits": 900,
        "price": 74.95,
        "price_yearly": 599.95,
        "features": [
            "900 créditos/mês",
            "15 cortes por vídeo",
            "Legendas personalizadas",
            "Download em 4K",
            "AI Reframe (face tracking)",
            "Brand Kit completo",
            "Publicação em redes sociais",
            "Edição em massa",
            "API access",
            "Suporte VIP",
        ],
        "limits": {
            "max_video_duration": 10800,  # 3 hours
            "max_clips_per_video": 15,
            "max_projects": -1,  # Unlimited
        }
    }
}


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

    # Plan details
    plan_id = Column(String(50), default=PlanType.FREE.value)
    is_yearly = Column(Boolean, default=False)

    # Billing
    stripe_customer_id = Column(String(255), nullable=True)
    stripe_subscription_id = Column(String(255), nullable=True)
    mercadopago_subscription_id = Column(String(255), nullable=True)

    # Status
    status = Column(String(50), default="active")  # active, cancelled, past_due, trialing
    trial_ends_at = Column(DateTime, nullable=True)

    # Billing cycle
    current_period_start = Column(DateTime, nullable=True)
    current_period_end = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    user = relationship("User", back_populates="subscription")

    def __repr__(self):
        return f"<Subscription {self.id}: {self.plan_id} for user {self.user_id}>"

    @property
    def plan(self) -> dict:
        """Get plan details"""
        return PLANS.get(self.plan_id, PLANS["free"])

    @property
    def is_active(self) -> bool:
        """Check if subscription is active"""
        if self.status not in ["active", "trialing"]:
            return False
        if self.current_period_end and datetime.utcnow() > self.current_period_end:
            return False
        return True

    @property
    def monthly_credits(self) -> int:
        """Get monthly credits for this plan"""
        return self.plan.get("credits", 60)
