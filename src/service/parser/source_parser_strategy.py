"""Source parser strategy - selects appropriate parser for a source.

This module provides the main interface for parsing sources. It uses a registry
pattern where parsers register themselves using the @register_parser decorator.

Usage:
    from service.parser import get_parser_for_source, detect_source_type

    # Get parser for a source with known type
    parser = get_parser_for_source(source)
    items = parser.parse(source)

    # Auto-detect source type from URL
    source_type = detect_source_type(url)
"""

from model.source import Source, SourceType
from schemas import FeedItemIn

# Import parsers to trigger registration
from service.parser import (
    github_parser,  # noqa: F401
    hn_parser,  # noqa: F401
    reddit_parser,  # noqa: F401
    rss_parser,  # noqa: F401
    telegram_parser,  # noqa: F401
    youtube_parser,  # noqa: F401
)
from service.parser.base import (
    BaseParser,
    detect_source_type,
    get_parser,
    get_registered_parsers,
)
from utils.logger import get_logger

logger = get_logger(__name__)

# Re-export for convenience
__all__ = [
    "get_parser_for_source",
    "detect_source_type",
    "get_registered_parsers",
    "parse_source_name",
    "BaseParser",
]


def get_parser_for_source(source: Source) -> BaseParser | None:
    """Get the appropriate parser for a source.

    Args:
        source: The source to get a parser for

    Returns:
        Parser instance or None if no parser found
    """
    parser = get_parser(source.source_type)
    if parser:
        return parser

    # Fallback: try auto-detection from URL
    detected_type = detect_source_type(source.resource_url)
    if detected_type:
        logger.info(f"Auto-detected source type: {detected_type} for {source.resource_url}")
        return get_parser(detected_type)

    # Final fallback: try RSS parser
    fallback_parser = get_parser(SourceType.RSS.value)
    if fallback_parser:
        logger.info(f"Falling back to RSS parser for {source.resource_url}")
        return fallback_parser

    return None


def parse_source_name(resource_url: str, source_type: str | None = None) -> str:
    """Generate a source name from URL.

    Uses the parser's get_source_name method if available,
    otherwise falls back to a generic name.
    """
    # Try explicit source type, then auto-detect
    effective_type = source_type or detect_source_type(resource_url)
    if effective_type:
        parser = get_parser(effective_type)
        if parser:
            return parser.get_source_name(resource_url)

    # Fallback: use domain
    from urllib.parse import urlparse

    parsed = urlparse(resource_url)
    return parsed.netloc.replace("www.", "")


def parse_source(source: Source) -> list[FeedItemIn]:
    """Parse a source and return feed items.

    Convenience function that gets the parser and calls parse().
    """
    parser = get_parser_for_source(source)
    if not parser:
        logger.warning(f"No parser found for source: {source.name} ({source.source_type})")
        return []

    return parser.parse(source)
