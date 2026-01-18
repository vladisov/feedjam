"""Base parser infrastructure with registry pattern.

To add a new parser:
1. Create a new file in service/parser/ (e.g., reddit_parser.py)
2. Implement a class that inherits from BaseParser
3. Register it with the @register_parser decorator
4. Add the source type to model/source.py SourceType enum

Example:
    from service.parser.base import BaseParser, register_parser

    @register_parser("reddit")
    class RedditParser(BaseParser):
        @classmethod
        def can_handle(cls, url: str) -> bool:
            return "reddit.com" in url

        def parse(self, source: Source) -> list[FeedItemIn]:
            # Implementation here
            ...
"""

from abc import ABC, abstractmethod
from datetime import datetime

from model.source import Source
from schemas import FeedItemIn
from utils.logger import get_logger

logger = get_logger(__name__)

# Parser registry - maps source_type to parser class
_PARSER_REGISTRY: dict[str, type["BaseParser"]] = {}


def register_parser(source_type: str):
    """Decorator to register a parser for a source type.

    Usage:
        @register_parser("hackernews")
        class HackerNewsParser(BaseParser):
            ...
    """

    def decorator(cls: type["BaseParser"]) -> type["BaseParser"]:
        _PARSER_REGISTRY[source_type] = cls
        logger.info(f"Registered parser: {source_type} -> {cls.__name__}")
        return cls

    return decorator


def get_parser(source_type: str) -> "BaseParser | None":
    """Get a parser instance for the given source type."""
    parser_cls = _PARSER_REGISTRY.get(source_type)
    if parser_cls:
        return parser_cls()
    return None


def get_registered_parsers() -> list[str]:
    """Get list of all registered source types."""
    return list(_PARSER_REGISTRY.keys())


def detect_source_type(url: str) -> str | None:
    """Auto-detect source type from URL.

    Iterates through registered parsers and returns the first
    one that can handle the URL. RSS is checked last as it's
    the most generic fallback parser.
    """
    # Check specific parsers first (not RSS)
    for source_type, parser_cls in _PARSER_REGISTRY.items():
        if source_type == "rss":
            continue  # Check RSS last
        if parser_cls.can_handle(url):
            return source_type

    # Check RSS parser last as fallback
    if "rss" in _PARSER_REGISTRY and _PARSER_REGISTRY["rss"].can_handle(url):
        return "rss"

    return None


class BaseParser(ABC):
    """Base class for all feed parsers.

    Subclasses must implement:
    - parse(): Parse the source and return feed items
    - can_handle(): Check if this parser can handle a URL (class method)
    """

    @classmethod
    @abstractmethod
    def can_handle(cls, url: str) -> bool:
        """Check if this parser can handle the given URL.

        Used for auto-detection of source type when subscribing.
        """
        ...

    @abstractmethod
    def parse(self, source: Source) -> list[FeedItemIn]:
        """Parse the source and return a list of feed items."""
        ...

    def get_source_name(self, url: str) -> str:
        """Generate a human-readable name from URL.

        Override in subclass for custom naming logic.
        """
        # Default: use the domain and path
        from urllib.parse import urlparse

        parsed = urlparse(url)
        path = parsed.path.strip("/").replace("/", "-") or "feed"
        return f"{parsed.netloc}-{path}"

    def _parse_published_date(self, entry, fallback_to_now: bool = True) -> datetime | None:
        """Extract published date from a feedparser entry.

        Tries published_parsed first, then updated_parsed.
        Returns current datetime if fallback_to_now is True and no date found.
        """
        for attr in ("published_parsed", "updated_parsed"):
            parsed = getattr(entry, attr, None)
            if parsed:
                try:
                    return datetime(*parsed[:6])
                except (TypeError, ValueError):
                    continue

        return datetime.now() if fallback_to_now else None
