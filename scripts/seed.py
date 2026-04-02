"""
Seed demo users (Viewer, Analyst, Admin) for local testing.

Run from project root:

    python -m scripts.seed
"""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import select

from app.database import SessionLocal, engine
from app.models import Base, User, UserRole


def main() -> None:
    Path("data").mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)

    session = SessionLocal()
    try:
        existing = session.scalar(select(User).where(User.username == "admin"))
        if existing:
            print("Seed skipped: users already present (found 'admin').")
            return

        users = [
            User(username="viewer1", role=UserRole.VIEWER, is_active=True),
            User(username="analyst1", role=UserRole.ANALYST, is_active=True),
            User(username="admin", role=UserRole.ADMIN, is_active=True),
        ]
        session.add_all(users)
        session.commit()

        print("Created users (use X-User-ID with these ids):")
        for username in ("viewer1", "analyst1", "admin"):
            u = session.scalar(select(User).where(User.username == username))
            if u:
                print(f"  id={u.id}  username={u.username!r}  role={u.role.value}")
    finally:
        session.close()


if __name__ == "__main__":
    main()
