"""Dashboard response models."""

from pydantic import BaseModel, Field

from app.schemas.record import RecordOut


class DashboardSummary(BaseModel):
    """Aggregated totals across all records."""

    total_income: float
    total_expense: float
    net_balance: float


class CategoryTotals(BaseModel):
    """Income and expense totals for one category."""

    category: str
    total_income: float = Field(ge=0)
    total_expense: float = Field(ge=0)
    net: float


class RecentActivity(BaseModel):
    """Five most recent financial records."""

    items: list[RecordOut]
