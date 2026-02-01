"""
ClipGenius - Authentication API Routes
"""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from models import get_db, User, Subscription, PLANS
from services.auth import AuthService
from .dependencies import get_current_user, get_current_active_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ============ Request Schemas ============

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, description="Mínimo 8 caracteres")
    name: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=8)


class UpdateProfileRequest(BaseModel):
    name: Optional[str] = None


# ============ Response Schemas ============

class UserResponse(BaseModel):
    id: int
    email: str
    name: Optional[str]
    credits: int
    is_premium: bool
    is_verified: bool
    streak_days: int
    total_clips_generated: int
    total_videos_processed: int
    created_at: datetime
    last_login_at: Optional[datetime]

    class Config:
        from_attributes = True


class AuthResponse(BaseModel):
    user: UserResponse
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class PlanResponse(BaseModel):
    id: str
    name: str
    credits: int
    price: float
    price_yearly: float
    features: list
    limits: dict


class SubscriptionResponse(BaseModel):
    plan: PlanResponse
    status: str
    is_yearly: bool
    current_period_end: Optional[datetime]

    class Config:
        from_attributes = True


class MeResponse(BaseModel):
    user: UserResponse
    subscription: Optional[SubscriptionResponse]


class CheckinResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    bonus: Optional[int] = None
    streak_bonus: Optional[int] = None
    total_bonus: Optional[int] = None
    streak_days: Optional[int] = None
    new_balance: Optional[int] = None


# ============ Endpoints ============

@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    db: Session = Depends(get_db)
):
    """
    Registrar nova conta.
    Recebe 60 créditos de boas-vindas.
    """
    try:
        user = AuthService.register_user(
            db=db,
            email=request.email,
            password=request.password,
            name=request.name
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    tokens = AuthService.create_tokens(user)

    return AuthResponse(
        user=UserResponse.model_validate(user),
        **tokens
    )


@router.post("/login", response_model=AuthResponse)
async def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Login com email e senha.
    Retorna tokens JWT.
    """
    user = AuthService.authenticate_user(db, request.email, request.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    tokens = AuthService.create_tokens(user)

    return AuthResponse(
        user=UserResponse.model_validate(user),
        **tokens
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Renovar access token usando refresh token.
    """
    tokens = AuthService.refresh_access_token(db, request.refresh_token)

    if not tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return TokenResponse(**tokens)


@router.get("/me", response_model=MeResponse)
async def get_me(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Obter dados do usuário autenticado.
    Inclui informações da assinatura.
    """
    # Get subscription
    subscription = db.query(Subscription).filter(
        Subscription.user_id == current_user.id
    ).first()

    subscription_response = None
    if subscription:
        plan_data = PLANS.get(subscription.plan_id, PLANS["free"])
        subscription_response = SubscriptionResponse(
            plan=PlanResponse(**plan_data),
            status=subscription.status,
            is_yearly=subscription.is_yearly,
            current_period_end=subscription.current_period_end
        )

    return MeResponse(
        user=UserResponse.model_validate(current_user),
        subscription=subscription_response
    )


@router.put("/me", response_model=UserResponse)
async def update_profile(
    request: UpdateProfileRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Atualizar perfil do usuário.
    """
    user = AuthService.update_user(
        db=db,
        user=current_user,
        name=request.name
    )

    return UserResponse.model_validate(user)


@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Alterar senha do usuário.
    """
    success = AuthService.change_password(
        db=db,
        user=current_user,
        old_password=request.old_password,
        new_password=request.new_password
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Senha atual incorreta"
        )

    return {"message": "Senha alterada com sucesso"}


@router.post("/checkin", response_model=CheckinResponse)
async def daily_checkin(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Check-in diário para ganhar créditos.
    +4 créditos por dia.
    Bônus de streak: 7 dias (+10), 30 dias (+50).
    """
    result = AuthService.daily_checkin(db, current_user)

    if not result["success"]:
        return CheckinResponse(success=False, message=result["message"])

    return CheckinResponse(
        success=True,
        bonus=result["bonus"],
        streak_bonus=result["streak_bonus"],
        total_bonus=result["total_bonus"],
        streak_days=result["streak_days"],
        new_balance=result["new_balance"]
    )


@router.get("/plans", response_model=list[PlanResponse])
async def list_plans():
    """
    Listar todos os planos disponíveis.
    """
    return [PlanResponse(**plan) for plan in PLANS.values()]
