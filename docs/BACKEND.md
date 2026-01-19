# Feedjam Backend Guidelines

## Tech Stack
- FastAPI 0.115+
- SQLAlchemy 2.0 (async-ready, sync for now)
- Pydantic 2.10+ for validation
- APScheduler for background tasks
- PostgreSQL 16 + Redis 7
- Poetry for dependency management
- Ruff for linting/formatting

## Project Structure
```
feedjam/
├── alembic/                # Database migrations (standard location)
│   └── versions/
├── alembic.ini
├── src/
│   ├── api/
│   │   ├── routers/        # Domain routers (users.py, feeds.py, etc.)
│   │   ├── exceptions.py   # Custom domain exceptions
│   │   └── schemas.py      # API-level schemas (ErrorResponse)
│   ├── model/              # SQLAlchemy ORM models
│   ├── repository/         # Data access layer (one per model)
│   ├── schemas/            # Pydantic schemas with In/Out naming
│   ├── service/            # Business logic layer
│   │   ├── llm/            # LLM integration (caching, batching, providers)
│   │   ├── parser/         # Source-specific parsers
│   │   ├── content_processor.py  # Content enrichment via LLM
│   │   └── factory.py      # ServiceFactory for background tasks
│   ├── tasks/              # APScheduler background tasks
│   ├── utils/
│   │   ├── config.py       # Environment configuration
│   │   ├── dependencies.py # FastAPI dependency injection
│   │   └── logger.py       # Centralized logging
│   └── main.py             # FastAPI app entry
```

## Schema Naming Convention
Use `In` suffix for input schemas, `Out` suffix for output schemas:
- `UserIn` - for creating/updating users
- `UserOut` - for returning user data
- `SubscriptionIn`, `SubscriptionOut`, `SubscriptionUpdate`

```python
# schemas/users.py
class UserIn(BaseModel):
    handle: str

class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    handle: str
    is_active: bool
    created_at: datetime
```

## Custom Exceptions
Use domain exceptions instead of HTTPException in services:
- `EntityNotFoundException(entity, identifier)` → 404
- `DuplicateEntityException(entity, field, value)` → 400
- `ValidationException(message)` → 400
- `ParserNotFoundException(source_type)` → 400
- `AuthException(message)` → 401
- `InvalidCredentialsException()` → 401
- `InvalidTokenException()` → 401

Exception handlers in main.py convert these to proper HTTP responses using a unified handler:

```python
# main.py - Single handler for all FeedJam exceptions
EXCEPTION_STATUS_CODES: dict[type[FeedJamException], int] = {
    EntityNotFoundException: 404,
    DuplicateEntityException: 400,
    ValidationException: 400,
    ParserNotFoundException: 400,
    AuthException: 401,
    InvalidCredentialsException: 401,
    InvalidTokenException: 401,
}

@app.exception_handler(FeedJamException)
async def feedjam_exception_handler(request: Request, exc: FeedJamException) -> JSONResponse:
    status_code = EXCEPTION_STATUS_CODES.get(type(exc), 500)
    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(message=exc.message, details=exc.details).model_dump(),
    )
```

## Authentication

FeedJam uses JWT-based authentication with access and refresh tokens.

### Overview
- **Access tokens**: Short-lived (30 min), used for API requests
- **Refresh tokens**: Long-lived (7 days), used to obtain new access tokens
- **Password hashing**: bcrypt via passlib
- **Token format**: JWT with HS256 algorithm

### Auth Schemas (`schemas/auth.py`)
```python
class UserRegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

class UserLoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)

class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshTokenIn(BaseModel):
    refresh_token: str

class AuthUserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    handle: str
    is_active: bool
    is_verified: bool
    created_at: datetime
```

### Auth Service (`service/auth_service.py`)
```python
class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt."""
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash."""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def create_access_token(user_id: int) -> str:
        """Create JWT access token (30 min expiry)."""
        ...

    @staticmethod
    def create_refresh_token(user_id: int) -> str:
        """Create JWT refresh token (7 day expiry)."""
        ...

    @staticmethod
    def decode_token(token: str, token_type: str = "access") -> int:
        """Decode token and return user_id. Raises InvalidTokenException on failure."""
        ...

    def register(self, data: UserRegisterIn) -> TokenOut:
        """Register new user, return tokens."""
        ...

    def login(self, data: UserLoginIn) -> TokenOut:
        """Authenticate user, return tokens."""
        ...

    def refresh_tokens(self, refresh_token: str) -> TokenOut:
        """Refresh access token using valid refresh token."""
        ...
```

### Auth Endpoints (`/auth`)
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/auth/register` | Register new user | No |
| POST | `/auth/login` | Login, get tokens | No |
| POST | `/auth/refresh` | Refresh access token | No (uses refresh token in body) |
| GET | `/auth/me` | Get current user info | Yes |

### Auth Dependency (`utils/dependencies.py`)
```python
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

security = HTTPBearer()

def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> int:
    """Extract and validate user_id from JWT token."""
    return AuthService.decode_token(credentials.credentials, token_type="access")
```

### Protecting Endpoints
```python
from utils.dependencies import get_current_user_id

@router.get("/feed")
def get_feed(
    user_id: int = Depends(get_current_user_id),
    feed_service: FeedService = Depends(get_feed_service),
):
    return feed_service.get_user_feed(user_id)
```

### User Model Auth Fields
```python
class User(Base):
    # ... existing fields
    email: Mapped[str | None] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str | None] = mapped_column(String(255))
    is_verified: Mapped[bool] = mapped_column(default=False)
```

### Security Best Practices
- **Password requirements**: Minimum 8 characters, maximum 128
- **JWT secret**: Must be set via `JWT_SECRET_KEY` env var in production
- **Token types**: Access and refresh tokens have different `type` claims to prevent misuse
- **Disabled accounts**: Login checks `is_active` flag
- **No password in responses**: Passwords are never returned in API responses

## Dependency Injection

`ServiceFactory` is the single source of truth for wiring dependencies.

### ServiceFactory

```python
# service/factory.py
class ServiceFactory:
    def __init__(self, db: Session) -> None:
        self.db = db

    @cached_property
    def user_storage(self) -> UserStorage:
        return UserStorage(self.db)

    @cached_property
    def feed_service(self) -> FeedService:
        return FeedService(self.feed_storage, ...)
```

### FastAPI Endpoints

`dependencies.py` wraps ServiceFactory for FastAPI:

```python
# utils/dependencies.py
def get_factory(db: Session = Depends(get_db)) -> ServiceFactory:
    return ServiceFactory(db)

def get_feed_service(factory: ServiceFactory = Depends(get_factory)):
    return factory.feed_service
```

Usage in routers:
```python
@router.get("/{user_id}")
def get_feed(user_id: int, feed_service: FeedService = Depends(get_feed_service)):
    return feed_service.get_user_feed(user_id)
```

### Background Tasks

Use ServiceFactory directly:
```python
from repository.db import get_db
from service.factory import ServiceFactory

def scheduled_feed_fetch():
    with get_db() as db:
        factory = ServiceFactory(db)
        factory.feed_service.fetch_all_feeds()
```

## Database Session Management

Two patterns for database sessions:

### FastAPI Endpoints (Dependency Injection)
Use `get_db()` generator - automatic transaction handling:
```python
from repository.db import get_db

@router.get("/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):
    # Auto-commits on success, auto-rollback on error
    ...
```

### Background Tasks & Startup (Context Manager)
Use `get_db_session()` context manager:
```python
from repository.db import get_db_session

def scheduled_task():
    with get_db_session() as db:
        factory = ServiceFactory(db)
        factory.feed_service.do_something()
```

## Repository Pattern

### Rules
- One repository class per model
- Simplified method names: `get()`, `create()`, `get_all()`, `get_by_*`
- Public methods return **Pydantic schemas** for API use
- Private helpers may return ORM models for service layer internal use

### Return Types
```python
class UserStorage:
    def get(self, user_id: int) -> UserOut | None:
        """Public method - returns schema."""
        user = self._get_orm(user_id)
        return UserOut.model_validate(user) if user else None

    def _get_orm(self, user_id: int) -> User | None:
        """Private helper - returns ORM for internal use."""
        return self.db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()

    def create(self, user: UserIn) -> UserOut:
        db_user = User(handle=user.handle)
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return UserOut.model_validate(db_user)
```

## Service Layer

### Principles
- Business logic lives here, not in routers
- Services use repositories, never access DB directly
- Raise domain exceptions, not HTTPException
- Dependencies injected via constructor

### Pattern
```python
class FeedService:
    def __init__(
        self,
        feed_storage: FeedStorage,
        subscription_storage: SubscriptionStorage,
        source_storage: SourceStorage,
        content_processor: ContentProcessor,
        ranking_service: RankingService,
        like_history_storage: LikeHistoryStorage,
    ):
        self.feed_storage = feed_storage
        self.subscription_storage = subscription_storage
        self.content_processor = content_processor
        # ... etc

    def get_feed(self, user_id: int) -> UserFeedOut:
        # Business logic here
        ...
```

## Router Pattern
- One router file per domain
- Routers handle HTTP concerns only
- Use dependency injection for repositories/services
- Minimal logic - delegate to services

```python
# api/routers/users.py
router = APIRouter(prefix="/users", tags=["users"])

@router.post("", response_model=UserOut)
def create_user(user: UserIn, user_storage: UserStorage = Depends(get_user_storage)):
    existing = user_storage.get_by_handle(user.handle)
    if existing:
        raise DuplicateEntityException("User", "handle", user.handle)
    return user_storage.create(user)
```

## Logging

Always use the centralized logger:
```python
from utils.logger import get_logger

logger = get_logger(__name__)

# Usage
logger.info("Processing subscription", extra={"subscription_id": sub_id})
logger.error("Failed to fetch feed", exc_info=True)
```

**Do NOT use** `logging.getLogger(__name__)` directly.

## Background Tasks (APScheduler)

### Adding a Scheduled Job
```python
# tasks/scheduler.py
from apscheduler.triggers.interval import IntervalTrigger
from repository.db import get_db_session
from service.factory import ServiceFactory

def fetch_feeds_job():
    """Each task creates fresh session via ServiceFactory."""
    with get_db() as db:
        factory = ServiceFactory(db)
        try:
            factory.feed_service.fetch_all_feeds()
        except Exception as e:
            logger.error(f"Feed fetch failed: {e}", exc_info=True)

# Register job
scheduler.add_job(
    fetch_feeds_job,
    trigger=IntervalTrigger(minutes=30),
    id="fetch_feeds",
    replace_existing=True,
)
```

### Best Practices
- Create fresh db session per task invocation
- Use ServiceFactory for dependency management
- Wrap task body in try/except with logging
- Use `replace_existing=True` to avoid duplicate jobs

## Parser System (Extensible)

FeedJam uses a registry pattern for parsers, making it easy to add new source types.

### Available Parsers
- `rss` - Generic RSS/Atom feeds (default fallback)
- `hackernews` - Hacker News RSS feeds (via hnrss.org)
- `telegram` - Telegram public channels (via /s/ embed page)
- `reddit` - Reddit subreddits and user feeds
- `youtube` - YouTube channel and playlist feeds
- `github` - GitHub releases, commits, and activity feeds
- `twitter` - Twitter/X accounts (via Nitter RSS proxy)

### Source Types
Defined in `model/source.py`:
```python
class SourceType(str, Enum):
    RSS = "rss"
    HACKERNEWS = "hackernews"
    TELEGRAM = "telegram"
    REDDIT = "reddit"
    YOUTUBE = "youtube"
    GITHUB = "github"
    TWITTER = "twitter"
```

### Adding a New Parser

**Step 1: Create the parser file** (`service/parser/myparser.py`):
```python
from service.parser.base import BaseParser, register_parser
from model.source import Source
from schemas import FeedItemIn

@register_parser("mytype")
class MyParser(BaseParser):
    """Parser for my feed type."""

    @classmethod
    def can_handle(cls, url: str) -> bool:
        """Auto-detect if URL is this feed type."""
        return "mysite.com" in url

    def parse(self, source: Source) -> list[FeedItemIn]:
        """Parse feed and return items."""
        items = []
        # ... fetch and parse ...
        return items

    def get_source_name(self, url: str) -> str:
        """Generate human-readable name from URL."""
        return "my-source-name"
```

**Step 2: Add the source type** (`model/source.py`):
```python
class SourceType(str, Enum):
    # ... existing types ...
    MYTYPE = "mytype"  # Add new type
```

**Step 3: Import the parser** (auto-registration):
Add import in `service/parser/__init__.py`:
```python
from service.parser import myparser  # noqa: F401
```

That's it! The parser is automatically registered and will:
- Be used when `source.source_type == "mytype"`
- Auto-detect matching URLs when subscribing
- Generate proper source names

### Parser Interface

```python
class BaseParser(ABC):
    @classmethod
    @abstractmethod
    def can_handle(cls, url: str) -> bool:
        """Return True if this parser can handle the URL."""
        ...

    @abstractmethod
    def parse(self, source: Source) -> list[FeedItemIn]:
        """Parse the source and return feed items."""
        ...

    def get_source_name(self, url: str) -> str:
        """Optional: Generate name from URL."""
        ...
```

### Using Parsers

```python
from service.parser import get_parser_for_source, detect_source_type

# Get parser for a source
parser = get_parser_for_source(source)
items = parser.parse(source)

# Auto-detect source type from URL
source_type = detect_source_type(url)  # Returns "reddit", "rss", etc.

# List registered parsers
from service.parser import get_registered_parsers
print(get_registered_parsers())
```

## Feed Storage

- **Deduplication**: Items checked by `local_id + source_name` first, then by `link` URL
- **Ordering**: By `published DESC NULLS LAST, created_at DESC`
- **Feed generation**: Preserves unread items, adds new items, applies ranking, saves as new active feed

## Database Migrations (Alembic)

Alembic is at project root (standard location). Migrations run automatically on container startup.

```bash
# Run migrations locally
poetry run alembic upgrade head

# Create new migration
poetry run alembic revision --autogenerate -m "Add new table"

# Rollback
poetry run alembic downgrade -1

# Show current state
poetry run alembic current
```

## LLM Service Architecture

The LLM integration (`src/service/llm/`) provides content processing with caching and batching for efficiency.

### Directory Structure
```
service/llm/
├── __init__.py      # Exports
├── config.py        # LLMConfig, ProcessedContent dataclasses
├── provider.py      # LLMProvider ABC + OpenAIProvider
├── cache.py         # Redis caching layer
├── batcher.py       # Token-aware request batching
├── prompts.py       # Prompt templates
└── service.py       # Main LLMService class
```

### LLMProvider (Abstract)
```python
class LLMProvider(ABC):
    @abstractmethod
    def complete(self, prompt: str, system: str | None = None) -> str | None:
        """Generate completion for prompt."""
        ...

    @abstractmethod
    def get_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Get embeddings for semantic similarity."""
        ...
```

### LLMService
Orchestrates caching, batching, and provider calls:
```python
class LLMService:
    def __init__(self, provider: LLMProvider, cache: LLMCache, config: LLMConfig):
        self.provider = provider
        self.cache = cache
        self.config = config

    def process_items(self, items: list[FeedItemIn]) -> list[ProcessedContent]:
        # 1. Check cache for existing results
        # 2. Batch uncached items (10 per request)
        # 3. Single LLM call per batch (summary + topics + quality)
        # 4. Cache results (7-day TTL)
        # 5. Return enriched content
```

### ContentProcessor
High-level interface used by FeedService:
```python
class ContentProcessor:
    def __init__(self, llm_service: LLMService | None = None):
        # Auto-creates LLMService from env config if not provided

    def process_items(self, items: list[FeedItemIn]) -> list[FeedItemIn]:
        """Enrich items with summaries, topics, quality scores."""
        ...

    def get_embeddings(self, items: list[FeedItemIn]) -> list[list[float]]:
        """Get embeddings for semantic ranking."""
        ...
```

### Usage in FeedService
```python
def fetch_and_save_items(self, subscription_id: int):
    items = parser.parse(source)
    if config.ENABLE_SUMMARIZATION and items:
        items = self.content_processor.process_items(items)
    # ... save items
```

### Efficiency Features
- **Batching**: 10 items per LLM request (configurable via `LLM_BATCH_SIZE`)
- **Caching**: 7-day Redis cache keyed by content hash (configurable via `LLM_CACHE_TTL`)
- **Combined prompts**: Single call extracts summary + topics + quality score
- **Graceful degradation**: Returns original items if LLM fails

## User Settings & API Keys

Users can provide their own API keys for AI-powered features.

### Model
```python
class User(Base):
    # ... existing fields
    openai_api_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
```

### Schemas
```python
class UserSettingsIn(BaseModel):
    openai_api_key: str | None = None  # Set to empty string to remove

class UserSettingsOut(BaseModel):
    has_openai_key: bool = False  # Never expose actual key
```

### API Endpoints
```
GET  /users/{user_id}/settings     # Returns UserSettingsOut
PUT  /users/{user_id}/settings     # Accepts UserSettingsIn
```

### Security
- API keys are stored in the database (not exposed via API)
- `UserSettingsOut` only returns `has_openai_key: bool`
- Keys are never logged or returned to clients

## Configuration

All environment variables accessed via `utils/config.py`:

```python
# utils/config.py
import os

# Database
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./test.db")
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

# LLM Configuration
OPEN_AI_KEY = os.environ.get("OPEN_AI_KEY", "")  # Default API key (fallback)
LLM_MODEL = os.environ.get("LLM_MODEL", "gpt-4o-mini")
LLM_EMBEDDING_MODEL = os.environ.get("LLM_EMBEDDING_MODEL", "text-embedding-3-small")
LLM_BATCH_SIZE = int(os.environ.get("LLM_BATCH_SIZE", "10"))
LLM_CACHE_TTL = int(os.environ.get("LLM_CACHE_TTL", "604800"))  # 7 days

# Feature Flags
CREATE_ITEMS_ON_STARTUP = os.environ.get("CREATE_ITEMS_ON_STARTUP", "false").lower() == "true"
ENABLE_SUMMARIZATION = os.environ.get("ENABLE_SUMMARIZATION", "true").lower() == "true"
```

### Environment Variables Reference

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | - |
| `REDIS_URL` | Redis connection (for caching) | `redis://localhost:6379/0` |
| `JWT_SECRET_KEY` | **Required in production**. Secret for JWT signing | Random (dev only) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifetime | `30` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token lifetime | `7` |
| `OPEN_AI_KEY` | Default OpenAI API key | - |
| `LLM_MODEL` | Model for completions | `gpt-4o-mini` |
| `LLM_EMBEDDING_MODEL` | Model for embeddings | `text-embedding-3-small` |
| `LLM_BATCH_SIZE` | Items per LLM request | `10` |
| `LLM_CACHE_TTL` | Cache TTL in seconds | `604800` (7 days) |
| `ENABLE_SUMMARIZATION` | Enable LLM content processing | `true` |
| `CREATE_ITEMS_ON_STARTUP` | Fetch items on startup | `false` |

## Testing

### BaseTestCase Pattern
```python
class TestUserAPI(BaseTestCase):
    def test_create_user(self):
        response = self.client.post("/users/", json={"handle": "testuser"})
        assert response.status_code == 200
        assert response.json()["handle"] == "testuser"

    def test_get_user_not_found(self):
        response = self.client.get("/users/999")
        assert response.status_code == 404
```

### Using ServiceFactory in Tests
```python
class TestFeedService(BaseTestCase):
    @pytest.fixture(autouse=True)
    def setup(self):
        Base.metadata.create_all(bind=engine)
        self.db = next(override_get_db())
        self.factory = ServiceFactory(self.db, openai_key="")

        # Convenience aliases
        self.feed_service = self.factory.feed_service
        self.user_storage = self.factory.user_storage

        yield
        self.db.close()
        Base.metadata.drop_all(bind=engine)
```

### Factory Methods
Two modes for creating test data:

```python
# Via API (tests full stack)
user = self.create_user(handle="testuser")

# Direct to storage (faster, bypasses API)
user = self.create_user_direct(handle="testuser")
```

### Auth Test Helpers
```python
class BaseTestCase:
    def register_user(
        self,
        email: str = "test@example.com",
        password: str = "password123",
    ) -> tuple[AuthUserOut, str]:
        """Register a user and return user info and access token."""
        response = self.client.post("/auth/register", json={
            "email": email,
            "password": password,
        })
        access_token = response.json()["access_token"]
        me_response = self.client.get("/auth/me", headers={
            "Authorization": f"Bearer {access_token}"
        })
        user = AuthUserOut(**me_response.json())
        return user, access_token

    def auth_headers(self, token: str) -> dict[str, str]:
        """Return authorization headers for a token."""
        return {"Authorization": f"Bearer {token}"}
```

Usage in tests:
```python
class TestProtectedEndpoint(BaseTestCase):
    def test_feed_with_auth(self):
        user, token = self.register_user()
        response = self.client.get("/feed", headers=self.auth_headers(token))
        assert response.status_code == 200
```

### Running Tests
```bash
# All tests
poetry run pytest

# Specific file
poetry run pytest src/__tests__/ranking_test.py -v

# Auth tests only
poetry run pytest src/__tests__/test_auth.py -v

# With coverage
poetry run pytest --cov=src
```
