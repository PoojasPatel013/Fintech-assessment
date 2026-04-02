"""FastAPI application entrypoint."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from app.config import get_settings
from app.database import engine
from app.models import Base
from app.routers import dashboard, records, users


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Create database tables on startup (SQLite file in ./data by default)."""
    settings = get_settings()
    if settings.database_url.startswith("sqlite"):
        Path("data").mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Finance Dashboard API",
    description="Mock header auth (X-User-ID) and RBAC for financial records.",
    version="1.0.0",
    lifespan=lifespan,
)

API_PREFIX = "/api/v1"
app.include_router(users.router, prefix=API_PREFIX, tags=["users"])
app.include_router(records.router, prefix=API_PREFIX, tags=["records"])
app.include_router(dashboard.router, prefix=API_PREFIX, tags=["dashboard"])


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    """Liveness check for Docker and load balancers."""
    return {"status": "ok"}
