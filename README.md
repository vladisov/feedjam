# feedjam

Personal feed aggregation and personalization service. Aggregates content from various sources (RSS, Telegram, Hacker News) and uses AI to personalize your feed.

## Prerequisites

- Python 3.12+
- Poetry
- Docker & Docker Compose (for containerized setup)
- PostgreSQL 16+ (for local development without Docker)
- Redis 7+ (for local development without Docker)

## Quick Start with Docker

```bash
# Copy environment file
cp .env.example .env

# Edit .env with your settings (especially OPEN_AI_KEY)
nano .env

# Start all services
docker-compose up -d

# For development with hot reload
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

The API will be available at `http://localhost:8000`

## Local Development Setup

```bash
# Install Poetry (if not installed)
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install

# Copy environment file
cp .env.example .env

# Start Postgres and Redis (via Docker or locally)
docker-compose up -d db redis

# Run database migrations
poetry run alembic upgrade head

# Start development server
poetry run dev
```

## Available Commands

```bash
# Development server with hot reload
poetry run dev

# Linting
poetry run lint

# Auto-fix linting issues
poetry run lint-fix

# Format code
poetry run format

# Run tests
poetry run pytest

# Run specific test file
poetry run pytest src/__tests__/feed_service_test.py -v
```

## Project Structure

```
feedjam/
├── src/
│   ├── api/
│   │   ├── routers/        # API endpoint routers
│   │   ├── exceptions.py   # Custom domain exceptions
│   │   └── schemas.py      # API-level schemas (errors, responses)
│   ├── model/              # SQLAlchemy ORM models
│   ├── repository/         # Data access layer
│   ├── schemas/            # Pydantic schemas (In/Out naming)
│   ├── service/            # Business logic
│   │   ├── extractor/      # Content extraction strategies
│   │   └── parser/         # Source-specific parsers
│   ├── tasks/              # Background task scheduler (APScheduler)
│   ├── utils/              # Configuration, logging, helpers
│   ├── __tests__/          # Test suite
│   └── main.py             # FastAPI application entry
├── scripts/                # Poetry script entrypoints
├── migrations/             # Alembic database migrations
├── docker-compose.yml      # Production Docker setup
├── docker-compose.dev.yml  # Development overrides
├── pyproject.toml          # Poetry + Ruff configuration
└── alembic.ini             # Alembic configuration
```

## Database Migrations

```bash
# Create a new migration
poetry run alembic revision --autogenerate -m "Description of change"

# Apply migrations
poetry run alembic upgrade head

# Rollback one migration
poetry run alembic downgrade -1
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/users/` | Create a new user |
| GET | `/users/{id}` | Get user by ID |
| GET | `/users/handle/{handle}` | Get user by handle |
| POST | `/subscriptions/` | Create subscription |
| GET | `/subscriptions/` | List subscriptions |
| GET | `/feeds/{user_id}` | Get personalized feed for user |
| GET | `/runs/` | List feed fetch runs |
| GET | `/runs/{id}` | Get run details |

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | - |
| `REDIS_URL` | Redis connection string | - |
| `OPEN_AI_KEY` | OpenAI API key for personalization | - |
| `CREATE_ITEMS_ON_STARTUP` | Fetch items on app startup | `false` |
| `DEBUG` | Enable debug mode | `false` |

## Tech Stack

- **Framework**: FastAPI 0.115+
- **Database**: PostgreSQL 16 + SQLAlchemy 2.0
- **Cache/Queue**: Redis 7
- **Background Tasks**: APScheduler
- **AI**: OpenAI API
- **Validation**: Pydantic 2.10+
- **Linting**: Ruff
- **Testing**: pytest + pytest-asyncio
