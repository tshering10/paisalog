FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    UV_HTTP_TIMEOUT=120

WORKDIR /app

COPY --from=docker.io/astral/uv:latest /uv /uvx /bin/

COPY pyproject.toml uv.lock ./

# Persist package wheel cache across builds
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev


COPY app ./app
COPY scripts ./scripts
COPY alembic.ini ./
COPY alembic ./alembic

EXPOSE 8000

CMD ["uv", "run", "--no-dev", "fastapi", "run", "app/main.py", "--host", "0.0.0.0", "--port", "8000"]