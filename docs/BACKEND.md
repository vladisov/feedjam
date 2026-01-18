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
│   │   ├── parser/         # Source-specific parsers
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

Exception handlers in main.py convert these to proper HTTP responses using a unified handler:

```python
# main.py - Single handler for all FeedJam exceptions
EXCEPTION_STATUS_CODES: dict[type[FeedJamException], int] = {
    EntityNotFoundException: 404,
    DuplicateEntityException: 400,
    ValidationException: 400,
    ParserNotFoundException: 400,
}

@app.exception_handler(FeedJamException)
async def feedjam_exception_handler(request: Request, exc: FeedJamException) -> JSONResponse:
    status_code = EXCEPTION_STATUS_CODES.get(type(exc), 500)
    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(message=exc.message, details=exc.details).model_dump(),
    )
```

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
from repository.db import get_db_session
from service.factory import ServiceFactory

def scheduled_feed_fetch():
    with get_db_session() as db:
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
Use `get_db_session()` - manual transaction control:
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
        data_extractor: DataExtractor,
        ranking_service: RankingService,
        like_history_storage: LikeHistoryStorage,
    ):
        self.feed_storage = feed_storage
        self.subscription_storage = subscription_storage
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
    with get_db_session() as db:
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
- `hackernews` - Hacker News RSS feeds
- `telegram` - Telegram public channels
- `reddit` - Reddit subreddits and user feeds
- `youtube` - YouTube channel and playlist feeds
- `github` - GitHub releases, commits, and activity feeds

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

## External Service Integration

For API integrations (OpenAI, etc.):

```python
class DataExtractor:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = OpenAI(api_key=api_key)

    def summarize(self, content: str) -> str | None:
        """Graceful degradation - returns None on failure."""
        try:
            response = self.client.chat.completions.create(...)
            return response.choices[0].message.content
        except Exception as e:
            logger.warning(f"Summarization failed: {e}")
            return None
```

### Guidelines
- Inject API keys via constructor
- Log failures but don't crash
- Return None or default for optional features
- Consider feature flags for expensive operations

## Configuration

All environment variables accessed via `utils/config.py`:

```python
# utils/config.py
import os

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./test.db")
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
OPEN_AI_KEY = os.environ.get("OPEN_AI_KEY", "")
CREATE_ITEMS_ON_STARTUP = os.environ.get("CREATE_ITEMS_ON_STARTUP", "false").lower() == "true"
```

### Feature Flags
- `CREATE_ITEMS_ON_STARTUP` - Fetch items on app start (dev only)

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

### Running Tests
```bash
# All tests
poetry run pytest

# Specific file
poetry run pytest src/__tests__/ranking_test.py -v

# With coverage
poetry run pytest --cov=src
```
