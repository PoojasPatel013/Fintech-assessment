"""User management (Admin only)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_admin
from app.models import Record, User
from app.schemas.user import PaginatedUsers, UserCreate, UserOut, UserUpdate

router = APIRouter()


@router.post(
    "/users",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
) -> User:
    """Create a new user with username, role, and active status."""
    user = User(
        username=payload.username.strip(),
        role=payload.role,
        is_active=payload.is_active,
    )
    db.add(user)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists",
        ) from exc
    db.refresh(user)
    return user


@router.get(
    "/users",
    response_model=PaginatedUsers,
    dependencies=[Depends(require_admin)],
)
def list_users(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 20,
) -> PaginatedUsers:
    """List users with pagination."""
    if skip < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="skip must be >= 0",
        )
    if limit < 1 or limit > 200:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="limit must be between 1 and 200",
        )

    total = db.scalar(select(func.count()).select_from(User))
    rows = db.scalars(select(User).offset(skip).limit(limit)).all()
    return PaginatedUsers(
        items=[UserOut.model_validate(u) for u in rows],
        total=int(total or 0),
        skip=skip,
        limit=limit,
    )


@router.get(
    "/users/{user_id}",
    response_model=UserOut,
    dependencies=[Depends(require_admin)],
)
def get_user(user_id: int, db: Session = Depends(get_db)) -> User:
    """Get a single user by id."""
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


@router.put(
    "/users/{user_id}",
    response_model=UserOut,
    dependencies=[Depends(require_admin)],
)
def update_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
) -> User:
    """Update username, role, and/or active status."""
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if payload.username is not None:
        user.username = payload.username.strip()
    if payload.role is not None:
        user.role = payload.role
    if payload.is_active is not None:
        user.is_active = payload.is_active

    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists",
        ) from exc
    db.refresh(user)
    return user


@router.delete(
    "/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_admin)],
)
def delete_user(user_id: int, db: Session = Depends(get_db)) -> None:
    """Delete a user if they have no financial records."""
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    has_records = db.scalar(
        select(func.count()).select_from(Record).where(Record.user_id == user_id)
    )
    if has_records and int(has_records) > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete user with existing financial records",
        )

    db.delete(user)
