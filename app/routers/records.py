"""Financial records CRUD with RBAC."""

from datetime import date, datetime, time, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_admin, require_analyst_or_admin
from app.models import Record, RecordType, User
from app.schemas.record import PaginatedRecords, RecordCreate, RecordOut, RecordUpdate

router = APIRouter()


def _day_start_utc(d: date) -> datetime:
    return datetime.combine(d, time.min, tzinfo=timezone.utc)


def _day_end_utc(d: date) -> datetime:
    return datetime.combine(d, time.max, tzinfo=timezone.utc)


def _build_record_filters(
    category: str | None,
    record_type: RecordType | None,
    start_date: date | None,
    end_date: date | None,
) -> list:
    conditions = []
    if category is not None:
        conditions.append(Record.category == category)
    if record_type is not None:
        conditions.append(Record.type == record_type)
    if start_date is not None:
        conditions.append(Record.date >= _day_start_utc(start_date))
    if end_date is not None:
        conditions.append(Record.date <= _day_end_utc(end_date))
    return conditions


@router.post(
    "/records",
    response_model=RecordOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
def create_record(
    payload: RecordCreate,
    db: Session = Depends(get_db),
) -> Record:
    """Create a record (Admin only). ``user_id`` must reference an existing user."""
    owner = db.get(User, payload.user_id)
    if owner is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="user_id does not reference an existing user",
        )

    record = Record(
        amount=payload.amount,
        type=payload.type,
        category=payload.category,
        date=payload.date,
        notes=payload.notes,
        user_id=payload.user_id,
    )
    db.add(record)
    db.flush()
    db.refresh(record)
    return record


@router.get(
    "/records",
    response_model=PaginatedRecords,
    dependencies=[Depends(require_analyst_or_admin)],
)
def list_records(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 20,
    category: str | None = None,
    record_type: RecordType | None = Query(None, alias="type"),
    start_date: date | None = None,
    end_date: date | None = None,
) -> PaginatedRecords:
    """List records with pagination and optional filters (Analyst/Admin)."""
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
    if start_date is not None and end_date is not None and start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date must be on or before end_date",
        )

    filters = _build_record_filters(category, record_type, start_date, end_date)
    base = select(Record)
    count_stmt = select(func.count()).select_from(Record)
    if filters:
        base = base.where(and_(*filters))
        count_stmt = count_stmt.where(and_(*filters))

    total = db.scalar(count_stmt)
    rows = db.scalars(
        base.order_by(Record.date.desc(), Record.id.desc()).offset(skip).limit(limit)
    ).all()
    return PaginatedRecords(
        items=[RecordOut.model_validate(r) for r in rows],
        total=int(total or 0),
        skip=skip,
        limit=limit,
    )


@router.get(
    "/records/{record_id}",
    response_model=RecordOut,
    dependencies=[Depends(require_analyst_or_admin)],
)
def get_record(record_id: int, db: Session = Depends(get_db)) -> Record:
    """Get one record by id (Analyst/Admin)."""
    record = db.get(Record, record_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Record not found",
        )
    return record


@router.put(
    "/records/{record_id}",
    response_model=RecordOut,
    dependencies=[Depends(require_admin)],
)
def update_record(
    record_id: int,
    payload: RecordUpdate,
    db: Session = Depends(get_db),
) -> Record:
    """Update a record (Admin only)."""
    record = db.get(Record, record_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Record not found",
        )

    if payload.user_id is not None:
        owner = db.get(User, payload.user_id)
        if owner is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="user_id does not reference an existing user",
            )
        record.user_id = payload.user_id

    if payload.amount is not None:
        record.amount = payload.amount
    if payload.type is not None:
        record.type = payload.type
    if payload.category is not None:
        record.category = payload.category
    if payload.date is not None:
        record.date = payload.date
    if payload.notes is not None:
        record.notes = payload.notes

    db.flush()
    db.refresh(record)
    return record


@router.delete(
    "/records/{record_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_admin)],
)
def delete_record(record_id: int, db: Session = Depends(get_db)) -> None:
    """Delete a record (Admin only)."""
    record = db.get(Record, record_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Record not found",
        )
    db.delete(record)
