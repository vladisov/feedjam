# Multi-stage build for smaller production images
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry

# Copy dependency files
COPY pyproject.toml poetry.lock* ./

# Install dependencies (including dev for debugpy)
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

# Copy application code
COPY src/ ./src/
COPY alembic/ ./alembic/
COPY alembic.ini ./

ENV PYTHONPATH=/app/src

# Run migrations, then start with debugpy (attach-ready)
CMD alembic upgrade head && python -m debugpy --listen 0.0.0.0:5678 -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
