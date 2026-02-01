"""
ClipGenius - Authentication Service
JWT + bcrypt based authentication
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from config import JWT_SECRET_KEY, JWT_ALGORITHM, JWT_ACCESS_TOKEN_EXPIRE_MINUTES, JWT_REFRESH_TOKEN_EXPIRE_DAYS
from models import User, Subscription, CreditTransaction, CREDIT_BONUSES


# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def create_refresh_token(data: dict) -> str:
    """Create a JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        return None


class AuthService:
    """Service for user authentication operations"""

    @staticmethod
    def register_user(
        db: Session,
        email: str,
        password: str,
        name: Optional[str] = None
    ) -> User:
        """
        Register a new user with welcome bonus credits.
        Raises ValueError if email already exists.
        """
        # Check if email exists
        existing = db.query(User).filter(User.email == email.lower()).first()
        if existing:
            raise ValueError("Email already registered")

        # Create user
        user = User(
            email=email.lower(),
            password_hash=get_password_hash(password),
            name=name,
            credits=CREDIT_BONUSES["signup"],
        )
        db.add(user)
        db.flush()

        # Create free subscription
        subscription = Subscription(
            user_id=user.id,
            plan_id="free",
            status="active",
        )
        db.add(subscription)

        # Record signup bonus transaction
        transaction = CreditTransaction(
            user_id=user.id,
            amount=CREDIT_BONUSES["signup"],
            balance_after=user.credits,
            transaction_type="bonus",
            description="Bônus de boas-vindas",
        )
        db.add(transaction)

        db.commit()
        db.refresh(user)

        return user

    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
        """
        Authenticate a user by email and password.
        Returns the user if valid, None otherwise.
        """
        user = db.query(User).filter(User.email == email.lower()).first()
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        if not user.is_active:
            return None

        # Update last login
        user.last_login_at = datetime.utcnow()
        db.commit()

        return user

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return db.query(User).filter(User.id == user_id, User.is_active == True).first()

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """Get user by email"""
        return db.query(User).filter(User.email == email.lower()).first()

    @staticmethod
    def create_tokens(user: User) -> dict:
        """Create access and refresh tokens for user"""
        token_data = {"sub": str(user.id), "email": user.email}
        return {
            "access_token": create_access_token(token_data),
            "refresh_token": create_refresh_token(token_data),
            "token_type": "bearer",
        }

    @staticmethod
    def refresh_access_token(db: Session, refresh_token: str) -> Optional[dict]:
        """
        Refresh an access token using a refresh token.
        Returns new tokens if valid, None otherwise.
        """
        payload = decode_token(refresh_token)
        if not payload:
            return None
        if payload.get("type") != "refresh":
            return None

        user_id = payload.get("sub")
        if not user_id:
            return None

        user = AuthService.get_user_by_id(db, int(user_id))
        if not user:
            return None

        return AuthService.create_tokens(user)

    @staticmethod
    def change_password(db: Session, user: User, old_password: str, new_password: str) -> bool:
        """Change user password. Returns True if successful."""
        if not verify_password(old_password, user.password_hash):
            return False

        user.password_hash = get_password_hash(new_password)
        db.commit()
        return True

    @staticmethod
    def update_user(
        db: Session,
        user: User,
        name: Optional[str] = None,
    ) -> User:
        """Update user profile"""
        if name is not None:
            user.name = name

        user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def daily_checkin(db: Session, user: User) -> dict:
        """
        Process daily check-in for user.
        Returns bonus info or None if already checked in today.
        """
        today = datetime.utcnow().date()

        # Check if already checked in today
        if user.last_checkin_at and user.last_checkin_at.date() == today:
            return {"success": False, "message": "Você já fez check-in hoje"}

        # Check streak
        yesterday = today - timedelta(days=1)
        if user.last_checkin_at and user.last_checkin_at.date() == yesterday:
            user.streak_days += 1
        else:
            user.streak_days = 1

        # Calculate bonus
        bonus = CREDIT_BONUSES["daily_checkin"]
        streak_bonus = 0

        if user.streak_days == 7:
            streak_bonus = CREDIT_BONUSES["streak_7"]
        elif user.streak_days == 30:
            streak_bonus = CREDIT_BONUSES["streak_30"]

        total_bonus = bonus + streak_bonus

        # Add credits
        user.credits += total_bonus
        user.last_checkin_at = datetime.utcnow()

        # Record transaction
        description = f"Check-in diário (dia {user.streak_days})"
        if streak_bonus > 0:
            description += f" + bônus de streak"

        transaction = CreditTransaction(
            user_id=user.id,
            amount=total_bonus,
            balance_after=user.credits,
            transaction_type="bonus",
            description=description,
        )
        db.add(transaction)
        db.commit()

        return {
            "success": True,
            "bonus": bonus,
            "streak_bonus": streak_bonus,
            "total_bonus": total_bonus,
            "streak_days": user.streak_days,
            "new_balance": user.credits,
        }
