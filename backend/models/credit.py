"""
ClipGenius - Credit Transaction Model
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
import enum
from .database import Base


class TransactionType(str, enum.Enum):
    DEDUCTION = "deduction"      # Credit spent
    PURCHASE = "purchase"        # Credit purchased
    BONUS = "bonus"              # Bonus credits (signup, checkin, etc.)
    REFUND = "refund"            # Credit refunded
    SUBSCRIPTION = "subscription"  # Monthly subscription credits


class CreditTransaction(Base):
    __tablename__ = "credit_transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Transaction details
    amount = Column(Integer, nullable=False)  # Positive = add, Negative = deduct
    balance_after = Column(Integer, nullable=False)  # Balance after transaction
    transaction_type = Column(String(50), nullable=False)

    # Reference (what caused this transaction)
    reference_type = Column(String(50), nullable=True)  # project, clip, subscription, etc.
    reference_id = Column(Integer, nullable=True)

    # Description
    description = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    user = relationship("User", back_populates="credit_transactions")

    def __repr__(self):
        return f"<CreditTransaction {self.id}: {self.amount} credits for user {self.user_id}>"


# Credit costs configuration
CREDIT_COSTS = {
    "process_video": 10,       # Processing a video (download + transcribe + analyze)
    "generate_clip": 2,        # Each clip generated
    "export_format": 1,        # Export to different format
    "apply_brand_kit": 1,      # Apply brand kit to clip
    "social_publish": 1,       # Publish to social media
}

# Credit bonus amounts
CREDIT_BONUSES = {
    "signup": 60,              # Welcome bonus
    "daily_checkin": 4,        # Daily check-in bonus
    "referral": 20,            # Referral bonus
    "streak_7": 10,            # 7-day streak bonus
    "streak_30": 50,           # 30-day streak bonus
}
