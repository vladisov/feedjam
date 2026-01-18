"""API-level schemas for requests and responses."""

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Standardized error response."""

    message: str
    details: dict | None = None


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
