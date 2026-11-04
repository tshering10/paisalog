# PaisaLog

PaisaLog is a full-stack personal finance tracker built with a **FastAPI** backend and a **Next.js 16** frontend. It covers authentication, email verification, category management, transaction CRUD, and financial analytics.

## Features

### Authentication & Account Management
- JWT authentication stored in an `httpOnly` cookie.
- User registration, login, current-user lookup, and logout.
- **Email verification** — new accounts start unverified; a verification link is sent on registration.
- Unverified users can log in but financial features (categories, transactions, analytics) are locked behind a `403` until the email is confirmed.
- **Email change** — request a change (with password confirmation), verify the new address, then the swap is applied atomically.
- Password reset via email link with rate limiting.
- Account deactivation (soft-delete) and reactivation via email link.
- Account deletion.
- Session listing and per-session revocation.
- Profile display-name update.

### Financial Features
- System and user-owned custom categories.
- Category creation, listing, renaming, and deletion.
- Income and expense transaction CRUD.
- Transaction ownership and category/type validation.
- Transaction filtering (`type`, `category_id`, `date_from`, `date_to`) and pagination.
- Monthly income, expense, net, and count summaries.
- Expense totals grouped by category.
- Monthly income and expense trends.

### Infrastructure
- PostgreSQL database managed with SQLAlchemy and Alembic.
- SMTP email delivery (Mailpit for local development).
- Rate limiting on all token-issuance endpoints.

---

## Project Structure

```text
Paisalog/
├── backend/
│   ├── app/
│   │   ├── api/                 # FastAPI dependencies and route handlers
│   │   │   ├── dependencies.py  # CurrentUser, VerifiedCurrentUser
│   │   │   └── routers/
│   │   │       └── endpoints/   # auth, categories, transactions, analytics
│   │   ├── core/                # Settings (config.py) and security utilities
│   │   ├── db/                  # SQLAlchemy engine and base
│   │   ├── models/              # Database models (User, Category, Transaction, …)
│   │   ├── schemas/             # Pydantic request and response schemas
│   │   └── services/            # Business logic (auth, verification, email, …)
│   ├── alembic/                 # Database migrations
│   │   └── versions/
│   ├── scripts/                 # Seed scripts
│   └── tests/                   # Pytest test suite
├── frontend/
│   └── src/
│       ├── app/
│       │   ├── (auth)/          # login, register, verify-email, verify-email-change,
│       │   │                    # forgot-password, reset-password, reactivate-account
│       │   └── (app)/           # dashboard, categories, transactions,
│       │                        # settings/profile, settings/security
│       ├── components/          # Shared UI components (app-shell, forms, …)
│       └── lib/                 # API client helpers (auth-api.ts, …)
├── docs/                        # Requirements and architecture decisions
└── compose.yaml                 # API, PostgreSQL, and Mailpit services
```

---

## Local Setup

### Requirements

- Python 3.12+ and [`uv`](https://github.com/astral-sh/uv)
- Node.js 20+ and `pnpm` (or `npm`)
- PostgreSQL, or Docker Desktop (recommended)

### Backend

Install dependencies:

```powershell
cd backend
uv sync --dev
```

Copy the environment template to the project root and fill in the values:

```powershell
Copy-Item .env.example ..\.env
```

The root `.env` must include:

```env
DATABASE_URL=postgresql+psycopg://paisalog:paisalog@localhost:5432/paisalog
TEST_DATABASE_URL=postgresql+psycopg://paisalog:paisalog@localhost:5432/paisalog_test
SECRET_KEY=replace-with-a-long-random-secret
COOKIE_SECURE=false
COOKIE_SAMESITE=lax
CORS_ORIGINS=http://localhost:3000
FRONTEND_URL=http://localhost:3000

# SMTP (Mailpit handles this automatically when using Docker)
# Use "mailpit" with Docker Compose; use "localhost" when running the API on the host.
SMTP_HOST=mailpit
SMTP_PORT=1025
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_USE_TLS=false
EMAIL_FROM=noreply@paisalog.local

# Token settings (defaults shown — can be omitted)
PASSWORD_RESET_TOKEN_EXPIRE_MINUTES=5
PASSWORD_RESET_RATE_LIMIT_COUNT=3
PASSWORD_RESET_RATE_LIMIT_WINDOW_MINUTES=15
ACCOUNT_REACTIVATION_TOKEN_EXPIRE_MINUTES=30
ACCOUNT_REACTIVATION_RATE_LIMIT_COUNT=3
ACCOUNT_REACTIVATION_RATE_LIMIT_WINDOW_MINUTES=15
EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES=1440
EMAIL_VERIFICATION_RATE_LIMIT_COUNT=3
EMAIL_VERIFICATION_RATE_LIMIT_WINDOW_MINUTES=15
EMAIL_CHANGE_TOKEN_EXPIRE_MINUTES=60
EMAIL_CHANGE_RATE_LIMIT_COUNT=3
EMAIL_CHANGE_RATE_LIMIT_WINDOW_MINUTES=15
```

> **Never commit `.env` or real secrets.**

### Frontend

Install dependencies:

```powershell
cd frontend
pnpm install
```

Copy the frontend environment file:

```powershell
Copy-Item .env.example .env.local
```

```env
BACKEND_URL=http://localhost:8000
```

When running the backend on the host instead of Docker, change `SMTP_HOST` in the
root `.env` to `localhost`.

---

## Run with Docker (Recommended)

Docker Compose starts the API, PostgreSQL, and Mailpit together.

```powershell
docker compose up --build -d
```

Apply all database migrations:

```powershell
docker compose exec api uv run alembic upgrade head
```

Seed the default system categories:

```powershell
docker compose exec api uv run python -m scripts.seed
```

Open the Mailpit inbox to inspect outgoing emails (verification links, password resets):

```
http://localhost:8025
```

Stop all services:

```powershell
docker compose down
```

The API is available at `http://localhost:8000`.

> **Migrations vs. rebuild** — You only need `docker compose up --build` when `Dockerfile` or `requirements` change. For a new migration, just run `alembic upgrade head` against the already-running container.

---

## Run Without Docker

### Backend

```powershell
uv run --directory backend fastapi dev app/main.py
```

Interactive API docs:

| UI | URL |
|----|-----|
| Swagger UI | http://127.0.0.1:8000/docs |
| ReDoc | http://127.0.0.1:8000/redoc |
| OpenAPI JSON | http://127.0.0.1:8000/openapi.json |
| Health check | http://127.0.0.1:8000/api/v1/health |

### Frontend

```powershell
cd frontend
pnpm dev
```

Open `http://localhost:3000`.

---

## Database Migrations

Create a new migration after changing a model:

```powershell
docker compose exec api uv run alembic revision --autogenerate -m "describe the change"
```

Apply pending migrations:

```powershell
docker compose exec api uv run alembic upgrade head
```

Check the current migration revision:

```powershell
docker compose exec api uv run alembic current
```

---

## Tests

Tests run from the `backend` directory and require a running PostgreSQL instance.

```powershell
cd backend
uv run pytest -v
```

When PostgreSQL is running in Docker but pytest runs on the host (Windows), the test database URL must use `localhost` instead of Docker's internal hostname:

```powershell
$testUrl = ((Get-Content ..\.env | Where-Object {
    $_ -match '^TEST_DATABASE_URL='
}) -split '=', 2)[1]
$env:TEST_DATABASE_URL = $testUrl -replace '@postgres:', '@localhost:'
uv run pytest -v
```

Lint and format checks:

```powershell
uv run ruff check app tests
uv run ruff format --check app tests
```

Frontend type-check and lint:

```powershell
cd frontend
pnpm tsc --noEmit
pnpm lint
```

---

## API Endpoints

All endpoints use the `/api/v1` prefix.

### Authentication & Account

```text
POST   /api/v1/auth/register                 Register (sends verification email)
POST   /api/v1/auth/login
GET    /api/v1/auth/me
POST   /api/v1/auth/logout
POST   /api/v1/auth/change-password
PATCH  /api/v1/auth/profile                  Update display name
POST   /api/v1/auth/deactivate
DELETE /api/v1/auth/account
```

### Email Verification

```text
POST   /api/v1/auth/verify-email             Confirm token from verification email
POST   /api/v1/auth/verify-email/resend      Resend verification email (rate-limited)
```

### Email Change  *(requires verified account)*

```text
POST   /api/v1/auth/email-change/request     Request change (sends link to new address)
POST   /api/v1/auth/email-change/confirm     Confirm token — swaps email atomically
```

### Password Reset

```text
POST   /api/v1/auth/forgot-password
POST   /api/v1/auth/reset-password
```

### Account Reactivation

```text
POST /api/v1/auth/reactivation/request
POST /api/v1/auth/reactivation/confirm
```

### Sessions

```text
GET    /api/v1/auth/sessions
DELETE /api/v1/auth/sessions/{session_id}
```

### Categories  *(requires verified account)*

```text
GET    /api/v1/categories
POST   /api/v1/categories
PATCH  /api/v1/categories/{category_id}
DELETE /api/v1/categories/{category_id}
```

### Transactions  *(requires verified account)*

```text
POST   /api/v1/transactions
GET    /api/v1/transactions             ?type, category_id, date_from, date_to, page, page_size
GET    /api/v1/transactions/{id}
PATCH  /api/v1/transactions/{id}
DELETE /api/v1/transactions/{id}
```

### Analytics  *(requires verified account)*

```text
GET    /api/v1/analytics/summary              ?year, month
GET    /api/v1/analytics/expenses-by-category ?year, month
GET    /api/v1/analytics/monthly-trend        ?year, month, months (1–24)
```

---

## Email Verification Flow

```
Register → session cookie issued (unverified)
         → verification email sent
         → user sees "Check your email" screen

User clicks link → GET /verify-email?token=...
                 → POST /api/v1/auth/verify-email
                 → email_verified_at set → full access granted

Unverified users see an amber banner in the dashboard with a "Resend link" button.
Categories, transactions, and analytics return 403 until verified.
```

## Email Change Flow

```
Settings → enter new email + current password
         → POST /api/v1/auth/email-change/request
         → pending_email stored; link sent to new address

User clicks link in new inbox → POST /api/v1/auth/email-change/confirm
                              → email swapped, token_version rotated
                              → all other sessions invalidated
```

---

## Frontend Integration

The backend sets an `httpOnly` JWT cookie. All browser requests must include credentials:

```javascript
fetch("http://localhost:8000/api/v1/auth/me", {
  credentials: "include",
});
```

For local frontend development, keep:

```env
CORS_ORIGINS=http://localhost:3000
```

The production setup uses a same-origin reverse proxy so `/api/*` requests go to the backend without CORS headers.
