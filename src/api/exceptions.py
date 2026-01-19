"""Custom domain exceptions.

These exceptions are raised in the service layer and converted to HTTP responses
by the exception handlers in main.py.
"""


class FeedJamException(Exception):
    """Base exception for all FeedJam errors."""

    def __init__(self, message: str, details: dict | None = None):
        self.message = message
        self.details = details or {}
        super().__init__(message)


class EntityNotFoundException(FeedJamException):
    """Raised when a requested entity is not found."""

    def __init__(self, entity: str, identifier: str | int):
        super().__init__(
            message=f"{entity} not found",
            details={"entity": entity, "identifier": str(identifier)},
        )


class ValidationException(FeedJamException):
    """Raised when validation fails."""

    def __init__(self, message: str, field: str | None = None):
        details = {"field": field} if field else {}
        super().__init__(message=message, details=details)


class DuplicateEntityException(FeedJamException):
    """Raised when trying to create a duplicate entity."""

    def __init__(self, entity: str, field: str, value: str):
        super().__init__(
            message=f"{entity} with {field}='{value}' already exists",
            details={"entity": entity, "field": field, "value": value},
        )


class ParserNotFoundException(FeedJamException):
    """Raised when no parser is available for a source."""

    def __init__(self, source_type: str):
        super().__init__(
            message=f"No parser available for source type: {source_type}",
            details={"source_type": source_type},
        )


class AuthException(FeedJamException):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message=message, details={"error": "auth_error"})


class InvalidCredentialsException(AuthException):
    """Raised when login credentials are invalid."""

    def __init__(self):
        super().__init__(message="Invalid email or password")


class InvalidTokenException(AuthException):
    """Raised when a token is invalid or expired."""

    def __init__(self):
        super().__init__(message="Invalid or expired token")
