from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.exceptions import (
    AuthException,
    DuplicateEntityException,
    EntityNotFoundException,
    FeedJamException,
    InvalidCredentialsException,
    InvalidTokenException,
    ParserNotFoundException,
    ValidationException,
)
from api.routers import (
    auth_router,
    feeds_router,
    runs_router,
    subscriptions_router,
    users_router,
    webhooks_router,
)
from api.schemas import ErrorResponse, HealthResponse
from utils.config import CREATE_ITEMS_ON_STARTUP
from utils.logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan events."""
    # Startup
    logger.info("Starting FeedJam API...")

    if CREATE_ITEMS_ON_STARTUP:
        from startup_runner import on_startup

        on_startup(app)

    # Start background scheduler
    from tasks.scheduler import start_scheduler, stop_scheduler

    start_scheduler()

    yield

    # Shutdown
    logger.info("Shutting down FeedJam API...")
    stop_scheduler()


app = FastAPI(
    title="FeedJam API",
    description="Personal feed aggregation and personalization",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Exception Handlers ---

# Maps exception types to HTTP status codes
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
    """Handle all FeedJam exceptions with appropriate status codes."""
    status_code = EXCEPTION_STATUS_CODES.get(type(exc), 500)
    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(message=exc.message, details=exc.details).model_dump(),
    )


# --- Routers ---

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(feeds_router)
app.include_router(subscriptions_router)
app.include_router(runs_router)
app.include_router(webhooks_router)


# --- Health Check ---


@app.get("/health", response_model=HealthResponse, tags=["health"])
def health_check() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(status="healthy", version="2.0.0")
