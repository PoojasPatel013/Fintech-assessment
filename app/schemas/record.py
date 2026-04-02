"""Financial record Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models import RecordType


class RecordCreate(BaseModel):
    """Payload to create a financial record."""

    amount: float = Field(..., gt=0)
    type: RecordType
    category: str = Field(..., min_length=1, max_length=128)
    date: datetime
    notes: str | None = Field(None, max_length=512)
    user_id: int = Field(
        ...,
        description="User this record belongs to (must exist).",
    )


class RecordUpdate(BaseModel):
    """Payload to update a record (all fields optional)."""

    amount: float | None = Field(None, gt=0)
    type: RecordType | None = None
    category: str | None = Field(None, min_length=1, max_length=128)
    date: datetime | None = None
    notes: str | None = Field(None, max_length=512)
    user_id: int | None = None


class RecordOut(BaseModel):
    """Record returned from the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    amount: float
    type: RecordType
    category: str
    date: datetime
    notes: str | None
    user_id: int


class PaginatedRecords(BaseModel):
    """Paginated list of records."""

    items: list[RecordOut]
    total: int
    skip: int
    limit: int
