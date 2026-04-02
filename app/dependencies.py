"""
Mock authentication (header-based) and role-based access control.

Authentication reads ``X-User-ID`` and loads the matching user from the database.
"""

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, UserRole


def get_current_user(
    db: Session = Depends(get_db),
    x_user_id: str | None = Header(None, alias="X-User-ID"),
) -> User:
    """
    Resolve the caller from the ``X-User-ID`` header (integer primary key).

    Returns 401 if the header is missing, invalid, or does not match a user.
    """
    if x_user_id is None or not str(x_user_id).strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-User-ID header",
        )
    try:
        uid = int(x_user_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-User-ID must be an integer",
        ) from exc

    user = db.get(User, uid)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found for X-User-ID",
        )
    return user


def require_active_user(user: User = Depends(get_current_user)) -> User:
    """Reject inactive users with 403."""
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )
    return user


def require_viewer_or_above(user: User = Depends(require_active_user)) -> User:
    """Allow Viewer, Analyst, and Admin (all authenticated active users)."""
    return user


def require_analyst_or_admin(user: User = Depends(require_active_user)) -> User:
    """Allow Analyst and Admin only."""
    if user.role not in (UserRole.ANALYST, UserRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Analyst or Admin role required",
        )
    return user


def require_admin(user: User = Depends(require_active_user)) -> User:
    """Allow Admin only."""
    if user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )
    return user
