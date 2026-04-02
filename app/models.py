"""SQLAlchemy ORM models."""

import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Declarative base for all models."""


class UserRole(str, enum.Enum):
    """Application roles (stored as strings in SQLite)."""

    VIEWER = "Viewer"
    ANALYST = "Analyst"
    ADMIN = "Admin"


class RecordType(str, enum.Enum):
    """Financial record type."""

    INCOME = "income"
    EXPENSE = "expense"


class User(Base):
    """Dashboard user with RBAC role and active flag."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, values_callable=lambda x: [e.value for e in x]),
        default=UserRole.VIEWER,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    records: Mapped[list["Record"]] = relationship("Record", back_populates="user")


class Record(Base):
    """Financial record linked to a user."""

    __tablename__ = "records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    type: Mapped[RecordType] = mapped_column(
        Enum(RecordType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    category: Mapped[str] = mapped_column(String(128), index=True)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    notes: Mapped[str | None] = mapped_column(String(512), nullable=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        index=True,
    )

    user: Mapped["User"] = relationship("User", back_populates="records")
