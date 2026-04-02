"""Dashboard aggregations and recent activity."""

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends

from app.database import get_db
from app.dependencies import require_analyst_or_admin, require_viewer_or_above
from app.models import Record, RecordType
from app.schemas.dashboard import CategoryTotals, DashboardSummary, RecentActivity
from app.schemas.record import RecordOut

router = APIRouter()


@router.get(
    "/dashboard/summary",
    response_model=DashboardSummary,
    dependencies=[Depends(require_viewer_or_above)],
)
def dashboard_summary(db: Session = Depends(get_db)) -> DashboardSummary:
    """Total income, total expense, and net balance (SQL aggregates)."""
    total_income = db.scalar(
        select(
            func.coalesce(
                func.sum(
                    case(
                        (Record.type == RecordType.INCOME, Record.amount),
                        else_=0,
                    )
                ),
                0,
            )
        )
    )
    total_expense = db.scalar(
        select(
            func.coalesce(
                func.sum(
                    case(
                        (Record.type == RecordType.EXPENSE, Record.amount),
                        else_=0,
                    )
                ),
                0,
            )
        )
    )
    ti = float(total_income or 0)
    te = float(total_expense or 0)
    return DashboardSummary(
        total_income=ti,
        total_expense=te,
        net_balance=ti - te,
    )


@router.get(
    "/dashboard/by-category",
    response_model=list[CategoryTotals],
    dependencies=[Depends(require_viewer_or_above)],
)
def dashboard_by_category(db: Session = Depends(get_db)) -> list[CategoryTotals]:
    """Per-category income and expense totals (GROUP BY category)."""
    income_case = case(
        (Record.type == RecordType.INCOME, Record.amount),
        else_=0,
    )
    expense_case = case(
        (Record.type == RecordType.EXPENSE, Record.amount),
        else_=0,
    )
    stmt = (
        select(
            Record.category,
            func.coalesce(func.sum(income_case), 0).label("total_income"),
            func.coalesce(func.sum(expense_case), 0).label("total_expense"),
        )
        .group_by(Record.category)
        .order_by(Record.category)
    )
    rows = db.execute(stmt).all()
    out: list[CategoryTotals] = []
    for row in rows:
        ti = float(row.total_income)
        te = float(row.total_expense)
        out.append(
            CategoryTotals(
                category=row.category,
                total_income=ti,
                total_expense=te,
                net=ti - te,
            )
        )
    return out


@router.get(
    "/dashboard/recent",
    response_model=RecentActivity,
    dependencies=[Depends(require_analyst_or_admin)],
)
def dashboard_recent(db: Session = Depends(get_db)) -> RecentActivity:
    """Five most recent records (Analyst/Admin)."""
    stmt = select(Record).order_by(Record.date.desc(), Record.id.desc()).limit(5)
    rows = db.scalars(stmt).all()
    return RecentActivity(
        items=[RecordOut.model_validate(r) for r in rows],
    )
