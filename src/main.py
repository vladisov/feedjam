from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.exceptions import (
    DuplicateEntityException,
    EntityNotFoundException,
    FeedJamException,
    ParserNotFoundException,
    ValidationException,
)
from api.routers import feeds_router, runs_router, subscriptions_router, users_router
from api.schemas import ErrorResponse, HealthResponse
from repository.db import Base, engine
from utils.config import CREATE_ITEMS_ON_STARTUP
from utils.logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan events."""
    # Startup
    logger.info("Starting FeedJam API...")
    Base.metadata.create_all(bind=engine)

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


@app.exception_handler(EntityNotFoundException)
async def entity_not_found_handler(request: Request, exc: EntityNotFoundException):
    return JSONResponse(
        status_code=404,
        content=ErrorResponse(message=exc.message, details=exc.details).model_dump(),
    )


@app.exception_handler(DuplicateEntityException)
async def duplicate_entity_handler(request: Request, exc: DuplicateEntityException):
    return JSONResponse(
        status_code=400,
        content=ErrorResponse(message=exc.message, details=exc.details).model_dump(),
    )


@app.exception_handler(ValidationException)
async def validation_handler(request: Request, exc: ValidationException):
    return JSONResponse(
        status_code=400,
        content=ErrorResponse(message=exc.message, details=exc.details).model_dump(),
    )


@app.exception_handler(ParserNotFoundException)
async def parser_not_found_handler(request: Request, exc: ParserNotFoundException):
    return JSONResponse(
        status_code=400,
        content=ErrorResponse(message=exc.message, details=exc.details).model_dump(),
    )


@app.exception_handler(FeedJamException)
async def feedjam_exception_handler(request: Request, exc: FeedJamException):
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(message=exc.message, details=exc.details).model_dump(),
    )


# --- Routers ---

app.include_router(users_router)
app.include_router(feeds_router)
app.include_router(subscriptions_router)
app.include_router(runs_router)


# --- Health Check ---


@app.get("/health", response_model=HealthResponse, tags=["health"])
def health_check():
    """Health check endpoint."""
    return HealthResponse(status="healthy", version="2.0.0")
