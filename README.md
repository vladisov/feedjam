# feedjam

Personal feed aggregation and personalization service. Aggregates content from various sources (RSS, Telegram, Hacker News, Reddit, YouTube, GitHub) and uses AI-powered ranking to personalize your feed.

## Prerequisites

- Python 3.12+
- Poetry
- Docker & Docker Compose (for containerized setup)
- PostgreSQL 16+ (for local development without Docker)
- Redis 7+ (for local development without Docker)

## Quick Start with Docker

```bash
# Copy environment file and edit settings
cp .env.example .env

# Start everything (migrations run automatically)
docker-compose up -d
```

The API will be available at `http://localhost:8001`

## Local Development Setup

```bash
# Install dependencies
poetry install

# Copy environment file
cp .env.example .env

# Start Postgres and Redis
docker-compose up -d db redis

# Run migrations
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

# Run tests with coverage
poetry run pytest --cov=src
```

## Project Structure

```
feedjam/
├── alembic/                # Database migrations (standard location)
│   ├── versions/           # Migration files
│   └── env.py              # Alembic environment
├── alembic.ini             # Alembic configuration
├── src/
│   ├── api/
│   │   ├── routers/        # API endpoint routers
│   │   ├── exceptions.py   # Custom domain exceptions
│   │   └── schemas.py      # API-level schemas (errors, responses)
│   ├── model/              # SQLAlchemy ORM models
│   ├── repository/         # Data access layer
│   ├── schemas/            # Pydantic schemas (In/Out naming)
│   ├── service/            # Business logic
│   │   ├── parser/         # Source-specific parsers
│   │   └── factory.py      # ServiceFactory for background tasks
│   ├── tasks/              # Background task scheduler (APScheduler)
│   ├── utils/
│   │   ├── config.py       # Environment configuration
│   │   ├── dependencies.py # FastAPI dependency injection
│   │   └── logger.py       # Centralized logging
│   ├── __tests__/          # Test suite
│   └── main.py             # FastAPI application entry
├── web/                    # React frontend
├── scripts/                # Poetry script entrypoints
├── docker-compose.yml      # Docker setup
├── docker-compose.dev.yml  # Development overrides
├── Dockerfile              # API container
└── pyproject.toml          # Poetry + Ruff configuration
```

## Database Migrations

Alembic is at project root (standard location). Migrations run automatically on container startup.

```bash
# Local development
poetry run alembic upgrade head

# Create a new migration
poetry run alembic revision --autogenerate -m "Description of change"

# Rollback one migration
poetry run alembic downgrade -1

# Check current status
poetry run alembic current
```

In Docker, migrations run automatically when the container starts.

## API Endpoints

### Users
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/users` | Create a new user |
| GET | `/users` | List all users |
| GET | `/users/{id}` | Get user by ID |
| GET | `/users/{id}/settings` | Get user settings |
| PUT | `/users/{id}/settings` | Update user settings (API keys) |

### User Interests (for personalized ranking)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/users/{id}/interests` | List user's interests |
| PUT | `/users/{id}/interests` | Replace all interests (bulk) |
| POST | `/users/{id}/interests` | Add single interest |
| DELETE | `/users/{id}/interests/{interest_id}` | Remove interest |

### Feed
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/feed/{user_id}` | Get personalized feed |
| POST | `/feed/{user_id}/mark-read/{item_id}` | Mark item as read |
| POST | `/feed/{user_id}/items/{item_id}/like` | Like an item |
| POST | `/feed/{user_id}/items/{item_id}/dislike` | Dislike an item |

### Subscriptions
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/subscriptions` | Create subscription |
| GET | `/subscriptions` | List subscriptions |
| DELETE | `/subscriptions/{id}` | Delete subscription |

### Runs (Feed fetch history)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/runs` | List feed fetch runs |
| GET | `/runs/{subscription_id}` | Get runs for subscription |
| POST | `/runs` | Trigger manual fetch |

### Email Inbox
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/users/me/inbox` | Get user's inbox address |
| POST | `/users/me/inbox/regenerate` | Regenerate inbox address |

### Webhooks
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/webhooks/inbound-email` | Receive emails (from Cloudflare worker) |

### Health
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |

## Supported Source Types

FeedJam auto-detects source types from URLs:

- **RSS** - Generic RSS/Atom feeds (fallback)
- **Hacker News** - hnrss.org feeds
- **Telegram** - Public Telegram channels
- **Reddit** - Subreddits and user feeds
- **YouTube** - Channel and playlist feeds
- **GitHub** - Releases, commits, activity feeds
- **Email** - Newsletter subscriptions via unique inbox address

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | - |
| `REDIS_URL` | Redis connection string | - |
| `OPEN_AI_KEY` | OpenAI API key for summarization | - |
| `CREATE_ITEMS_ON_STARTUP` | Fetch items on app startup | `false` |
| `DEBUG` | Enable debug mode | `false` |

## Personalized Ranking

FeedJam ranks feed items based on:

1. **User Interests** - Topics you care about (configurable via API)
2. **Source Affinity** - Sources you've liked/disliked in the past
3. **Popularity** - Points, views, engagement metrics
4. **Recency** - Newer items get a slight boost

See [docs/RANKING.md](docs/RANKING.md) for details on the ranking algorithm.

## Tech Stack

- **Framework**: FastAPI 0.115+
- **Database**: PostgreSQL 16 + SQLAlchemy 2.0
- **Cache/Queue**: Redis 7
- **Background Tasks**: APScheduler
- **AI**: OpenAI API (for summarization)
- **Validation**: Pydantic 2.10+
- **Linting**: Ruff
- **Testing**: pytest + pytest-asyncio
- **Frontend**: React + TypeScript + Vite

## Documentation

- [Backend Guidelines](docs/BACKEND.md) - Architecture, patterns, conventions
- [Frontend Guidelines](docs/FRONTEND.md) - React/TypeScript patterns
- [Ranking System](docs/RANKING.md) - How feed personalization works
