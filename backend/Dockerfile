FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN pip install --no-cache-dir uv \
    && uv sync --frozen --no-dev

COPY app ./app
COPY scripts ./scripts
COPY alembic.ini ./
COPY alembic ./alembic

EXPOSE 8000

CMD ["uv", "run", "--no-dev", "fastapi", "run", "app/main.py", "--host", "0.0.0.0", "--port", "8000"]