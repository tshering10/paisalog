# PaisaLog

PaisaLog is a personal finance tracker. The MVP backend provides
authentication, category management, transaction CRUD, and financial analytics
for a future Next.js frontend.

## MVP features

- JWT authentication stored in an `httpOnly` cookie.
- User registration, login, current-user lookup, and logout.
- System and user-owned custom categories.
- Category creation, listing, renaming, and deletion.
- Income and expense transaction CRUD.
- Transaction ownership and category/type validation.
- Transaction filtering and pagination.
- Monthly income, expense, net, and count summaries.
- Expense totals grouped by category.
- Monthly income and expense trends.
- PostgreSQL database managed with SQLAlchemy and Alembic.

## Project structure

```text
backend/
├── app/
│   ├── api/                 # FastAPI dependencies and route handlers
│   ├── core/                # Settings and security utilities
│   ├── db/                  # SQLAlchemy engine and base
│   ├── models/              # Database models
│   ├── schemas/             # Pydantic request and response schemas
│   └── services/            # Business logic and database queries
├── alembic/                 # Database migrations
├── scripts/                 # Development scripts
└── tests/                   # Pytest test suite
docs/                        # Requirements and architecture decisions
compose.yaml                 # API and PostgreSQL services
```

## Local setup

Requirements:

- Python 3.12+
- `uv`
- PostgreSQL, or Docker Desktop

Install backend dependencies:

```powershell
cd backend
uv sync --dev
```

Copy the environment template and update the values:

```powershell
Copy-Item ..\.env.example ..\.env
```

The root `.env` must include database URLs, a random `SECRET_KEY`, cookie
settings, and the frontend origin:

```env
DATABASE_URL=postgresql+psycopg://paisalog:password@localhost:5432/paisalog
TEST_DATABASE_URL=postgresql+psycopg://paisalog:password@localhost:5432/paisalog_test
SECRET_KEY=replace-with-a-long-random-secret
COOKIE_SECURE=false
COOKIE_SAMESITE=lax
CORS_ORIGINS=http://localhost:3000
```

Never commit `.env` or real secrets.

## Run with Docker

Start or rebuild the API and PostgreSQL services:

```powershell
docker compose up --build -d
```

Apply migrations:

```powershell
docker compose exec api uv run alembic upgrade head
```

Seed the default system categories:

```powershell
docker compose exec api uv run python -m scripts.seed
```

Stop the services:

```powershell
docker compose down
```

The Docker API is available at `http://localhost:8000`.

## Run locally without the API container

From the repository root:

```powershell
uv run --directory backend fastapi dev app/main.py
```

The interactive API documentation is available at:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`
- OpenAPI JSON: `http://127.0.0.1:8000/openapi.json`
- Health check: `http://127.0.0.1:8000/api/v1/health`

## Test

Tests run from the `backend` directory:

```powershell
cd backend
uv run pytest -v
```

When PostgreSQL is running in Docker but pytest runs on Windows, the test
database URL must use `localhost`, not Docker's internal hostname `postgres`.
For a temporary PowerShell override:

```powershell
$testUrl = ((Get-Content ..\.env | Where-Object {
    $_ -match '^TEST_DATABASE_URL='
}) -split '=', 2)[1]
$env:TEST_DATABASE_URL = $testUrl -replace '@postgres:', '@localhost:'
uv run pytest -v
```

Run lint and formatting checks:

```powershell
uv run ruff check app tests
uv run ruff format --check app tests
```

## API endpoints

All application endpoints use the `/api/v1` prefix.

### Authentication

```text
POST /api/v1/auth/register
POST /api/v1/auth/login
GET  /api/v1/auth/me
POST /api/v1/auth/logout
```

### Categories

```text
GET    /api/v1/categories
POST   /api/v1/categories
PATCH  /api/v1/categories/{category_id}
DELETE /api/v1/categories/{category_id}
```

### Transactions

```text
POST   /api/v1/transactions
GET    /api/v1/transactions
GET    /api/v1/transactions/{transaction_id}
PATCH  /api/v1/transactions/{transaction_id}
DELETE /api/v1/transactions/{transaction_id}
```

The transaction list supports `type`, `category_id`, `date_from`, `date_to`,
`page`, and `page_size`.

### Analytics

```text
GET /api/v1/analytics/summary
GET /api/v1/analytics/expenses-by-category
GET /api/v1/analytics/monthly-trend
```

Analytics endpoints require `year` and `month`. Monthly trend also accepts
`months` from 1 through 24.

## Frontend integration

The backend uses an `httpOnly` JWT cookie. Browser requests from the configured
frontend origin must include credentials:

```javascript
fetch("http://localhost:8000/api/v1/auth/me", {
  credentials: "include",
});
```

For local frontend development, keep:

```env
CORS_ORIGINS=http://localhost:3000
```

The planned production setup is a same-origin frontend proxy for `/api/*`.