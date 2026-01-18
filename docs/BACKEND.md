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
src/
├── api/
│   ├── routers/        # Domain routers (users.py, feeds.py, etc.)
│   ├── exceptions.py   # Custom domain exceptions
│   └── schemas.py      # API-level schemas (ErrorResponse)
├── model/              # SQLAlchemy ORM models
├── repository/         # Data access layer (one per model)
├── schemas/            # Pydantic schemas with In/Out naming
├── service/            # Business logic layer
├── tasks/              # APScheduler background tasks
├── utils/              # Config, logging, dependencies
└── main.py             # FastAPI app entry
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
- `DuplicateEntityException(entity, field, value)` → 409
- `ParserNotFoundException(source_type)` → 400

Exception handlers in main.py convert these to proper HTTP responses.

```python
# In service layer - raise domain exceptions
def get_user(self, user_id: int) -> UserOut:
    user = self.user_storage.get(user_id)
    if not user:
        raise EntityNotFoundException("User", user_id)
    return user

# In main.py - handle exceptions
@app.exception_handler(EntityNotFoundException)
async def entity_not_found_handler(request: Request, exc: EntityNotFoundException):
    return JSONResponse(status_code=404, content={"message": exc.message, "details": exc.details})
```

## Database Session Management

Two distinct patterns for database sessions:

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
        # Create fresh repositories/services per task
        user_storage = UserStorage(db)
        # Must explicitly manage transactions if needed
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
        subscription_storage: SubscriptionStorage,
        feed_storage: FeedStorage,
        source_storage: SourceStorage,
        data_extractor: DataExtractor,
    ):
        self.subscription_storage = subscription_storage
        self.feed_storage = feed_storage
        self.source_storage = source_storage
        self.data_extractor = data_extractor

    def get_feed(self, user_id: int) -> UserFeedOut:
        # Business logic here
        ...
```

### Dependency Injection
Services are instantiated in `utils/dependencies.py`:
```python
def get_feed_service(db: Session = Depends(get_db)) -> FeedService:
    return FeedService(
        subscription_storage=SubscriptionStorage(db),
        feed_storage=FeedStorage(db),
        source_storage=SourceStorage(db),
        data_extractor=DataExtractor(api_key=OPEN_AI_KEY),
    )
```

## Router Pattern
- One router file per domain
- Routers handle HTTP concerns only
- Use dependency injection for repositories/services
- Minimal logic - delegate to services

```python
# api/routers/users.py
router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=UserOut, status_code=201)
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

def fetch_feeds_job():
    """Each task creates fresh session and services."""
    with get_db_session() as db:
        feed_service = FeedService(
            subscription_storage=SubscriptionStorage(db),
            # ... other dependencies
        )
        try:
            feed_service.fetch_all_feeds()
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
- Wrap task body in try/except with logging
- Use `replace_existing=True` to avoid duplicate jobs

## Parser Strategy Pattern

Parsers extract feed items from different source types:

```python
# service/parser/source_parser_strategy.py
ParserFunc = Callable[[Source], list[FeedItemIn]]

PARSERS: dict[str, ParserFunc] = {
    "rss": parse_rss_feed,
    "telegram": parse_telegram_channel,
    "hackernews": parse_hackernews,
}

def get_parser(source: Source) -> ParserFunc:
    parser = PARSERS.get(source.source_type)
    if not parser:
        raise ParserNotFoundException(source.source_type)
    return parser
```

### Adding a New Parser
1. Create parser function in `service/parser/`
2. Return `list[FeedItemIn]` (input schemas, not ORM)
3. Register in `PARSERS` dict

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
ENABLE_SUMMARIZATION = os.environ.get("ENABLE_SUMMARIZATION", "true").lower() == "true"
```

### Feature Flags
- `CREATE_ITEMS_ON_STARTUP` - Fetch items on app start (dev only)
- `ENABLE_SUMMARIZATION` - Enable AI summarization

## Testing

### BaseTestCase Pattern
```python
class TestUserAPI(BaseTestCase):
    def test_create_user(self):
        response = self.client.post("/users/", json={"handle": "testuser"})
        assert response.status_code == 201
        assert response.json()["handle"] == "testuser"

    def test_get_user_not_found(self):
        response = self.client.get("/users/999")
        assert response.status_code == 404
```

### Factory Methods
Two modes for creating test data:

```python
# Via API (tests full stack)
user = self.create_user(handle="testuser")

# Direct to storage (faster, bypasses API)
user = self.create_user_direct(handle="testuser")
```

### Assertion Helpers
```python
self.assert_status(response, 201)
self.assert_error(response, 404, "User not found")
```
