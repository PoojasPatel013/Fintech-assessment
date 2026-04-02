"""User-related Pydantic schemas."""

from pydantic import BaseModel, ConfigDict, Field

from app.models import UserRole


class UserCreate(BaseModel):
    """Payload to create a user."""

    username: str = Field(..., min_length=1, max_length=128)
    role: UserRole = UserRole.VIEWER
    is_active: bool = True


class UserUpdate(BaseModel):
    """Payload to update a user (all fields optional)."""

    username: str | None = Field(None, min_length=1, max_length=128)
    role: UserRole | None = None
    is_active: bool | None = None


class UserOut(BaseModel):
    """User returned from the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    role: UserRole
    is_active: bool


class PaginatedUsers(BaseModel):
    """Paginated list of users."""

    items: list[UserOut]
    total: int
    skip: int
    limit: int
