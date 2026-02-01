"""
ClipGenius - API Dependencies
Authentication and authorization dependencies
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from models import get_db, User
from services.auth import decode_token, AuthService

# Bearer token security scheme
security = HTTPBearer(auto_error=False)


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Get current user from JWT token if provided.
    Returns None if no token or invalid token.
    Use this for optional authentication.
    """
    if not credentials:
        return None

    token = credentials.credentials
    payload = decode_token(token)

    if not payload:
        return None

    if payload.get("type") != "access":
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None

    user = AuthService.get_user_by_id(db, int(user_id))
    return user


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current user from JWT token.
    Raises HTTPException if not authenticated.
    Use this for required authentication.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas ou expiradas",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = credentials.credentials
    payload = decode_token(token)

    if not payload:
        raise credentials_exception

    if payload.get("type") != "access":
        raise credentials_exception

    user_id = payload.get("sub")
    if not user_id:
        raise credentials_exception

    user = AuthService.get_user_by_id(db, int(user_id))
    if not user:
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user.
    Raises HTTPException if user is deactivated.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Conta desativada"
        )
    return current_user


async def get_current_premium_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Get current user with premium subscription.
    Raises HTTPException if user is not premium.
    """
    if not current_user.is_premium:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Esta funcionalidade requer uma assinatura premium"
        )
    return current_user


def require_credits(amount: int):
    """
    Dependency factory that requires user to have minimum credits.

    Usage:
        @router.post("/endpoint")
        async def endpoint(user: User = Depends(require_credits(10))):
            ...
    """
    async def _require_credits(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        if not current_user.has_credits(amount):
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=f"Créditos insuficientes. Necessário: {amount}, disponível: {current_user.credits}"
            )
        return current_user

    return _require_credits
