# Finance Dashboard API

A compact **FastAPI** backend for a finance dashboard take-home: financial **records**, **role-based access control (RBAC)**, **admin user management**, and **dashboard aggregations** backed by **SQLite** via **SQLAlchemy 2.x**.

## Tech stack

| Piece | Why it is here |
|-------|----------------|
| **Python 3.12** | Widely used, readable, and easy for reviewers to run. |
| **FastAPI** | Automatic OpenAPI docs, validation with Pydantic, async-ready (this project uses sync SQLAlchemy for simplicity). |
| **SQLAlchemy 2.x** | Clear ORM models, explicit queries, portable SQL patterns. |
| **SQLite** | Single-file database, no separate DB service—fast setup for candidates and reviewers. |
| **Docker / Docker Compose** | Repeatable runs and a clear “works on my machine” baseline. |
| **GitHub Actions** | Lightweight CI (`flake8`, `black --check`) to show awareness of automated quality gates. |

The stack favors **simplicity** and **evaluation focus**: reviewers can run one command, open Swagger, and exercise RBAC without provisioning infrastructure.

## Assumptions

- **Authentication** is **mock header-based**: send `X-User-ID` with the integer primary key of an existing user. There is **no JWT** or password flow—this keeps tests and demos short.
- **Authorization** follows the stated roles:
  - **Viewer**: `GET /api/v1/dashboard/summary`, `GET /api/v1/dashboard/by-category` only.
  - **Analyst**: Viewer dashboard routes **plus** `GET` on records and `GET /api/v1/dashboard/recent`.
  - **Admin**: Analyst record reads **plus** `POST`/`PUT`/`DELETE` on records and **full CRUD** on `/api/v1/users`.
- **Database schema** is created with `create_all` on startup (**no Alembic** migrations) to keep the assessment small.
- **Record visibility**: Analysts and Admins listing or reading records see **all** records in the database (not scoped per-user), unless you extend the project.
- **Date filters** on `GET /api/v1/records`: `start_date` and `end_date` are **inclusive** calendar days in **UTC** (start-of-day through end-of-day).
- **Deleting users**: Users with existing financial records **cannot** be deleted until records are removed or reassigned (enforced with a `400` response and FK `RESTRICT`).

## Project layout

```
├── app/
│   ├── config.py          # Settings (e.g. DATABASE_URL)
│   ├── database.py        # Engine, session, get_db
│   ├── dependencies.py    # X-User-ID auth + RBAC
│   ├── models.py          # User, Record
│   ├── routers/
│   │   ├── users.py       # User CRUD (Admin only)
│   │   ├── records.py     # Record CRUD + filters
│   │   └── dashboard.py   # Aggregations + recent activity
│   └── schemas/           # Pydantic models
├── main.py                # FastAPI app + router includes
├── Dockerfile             # Multi-stage image
├── docker-compose.yml     # Volume for SQLite persistence
├── requirements.txt
└── scripts/seed.py        # Optional demo users
```

## Quick start (Docker Compose)

From the project root:

```bash
docker compose up --build
```

- API base URL: `http://localhost:8000`
- SQLite file (persisted on the host): `./data/app.db` (mounted into the container as `/app/data`)

Override the DB URL if needed:

```yaml
environment:
  DATABASE_URL: sqlite:////app/data/app.db
```

## Local development (without Docker)

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux / macOS

pip install -r requirements.txt
python -m scripts.seed          # optional: viewer, analyst, admin users
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Set `DATABASE_URL` in a `.env` file if you want a non-default path (see `app/config.py`).

## API documentation (Swagger UI)

With the app running:

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

Use **Authorize** / custom headers in Swagger: add header **`X-User-ID`** with a user id from `scripts/seed.py` (e.g. `3` for `admin`).

### Main endpoints

| Method | Path | Roles |
|--------|------|--------|
| GET | `/health` | Public |
| CRUD | `/api/v1/users` | **Admin** |
| CRUD | `/api/v1/records` | **GET**: Analyst, Admin — **Write**: Admin |
| GET | `/api/v1/dashboard/summary` | Viewer, Analyst, Admin |
| GET | `/api/v1/dashboard/by-category` | Viewer, Analyst, Admin |
| GET | `/api/v1/dashboard/recent` | Analyst, Admin |

**Records list filters** (query params): `category`, `type` (income/expense), `start_date`, `end_date` (dates), plus `skip` / `limit`.

## CI (lint)

GitHub Actions runs:

- `flake8 .`
- `black --check .`

Match line length and ignores via [`.flake8`](.flake8).

## License

Provided as an assessment template; adapt as needed for your organization.
