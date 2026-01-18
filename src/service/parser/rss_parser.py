"""Generic RSS/Atom feed parser."""

from urllib.parse import urlparse

import feedparser

from model.source import Source
from schemas import FeedItemIn
from service.parser.base import BaseParser, register_parser
from utils.logger import get_logger

logger = get_logger(__name__)


@register_parser("rss")
class RSSParser(BaseParser):
    """Generic parser for RSS and Atom feeds.

    This is the default fallback parser for any URL that looks like an RSS feed.
    It uses feedparser which handles RSS 0.9x, RSS 1.0, RSS 2.0, Atom 0.3, and Atom 1.0.
    """

    # Common RSS feed URL patterns
    RSS_PATTERNS = [
        "/rss",
        "/feed",
        "/atom",
        ".rss",
        ".xml",
        "/feeds/",
        "format=rss",
        "format=atom",
    ]

    @classmethod
    def can_handle(cls, url: str) -> bool:
        """Check if URL looks like an RSS feed.

        Returns True for URLs with common RSS patterns.
        This is the fallback parser, so it's permissive.
        """
        url_lower = url.lower()
        return any(pattern in url_lower for pattern in cls.RSS_PATTERNS)

    def parse(self, source: Source) -> list[FeedItemIn]:
        """Parse RSS/Atom feed."""
        feed = feedparser.parse(source.resource_url)

        if feed.bozo and not feed.entries:
            logger.warning(f"Feed parsing error for {source.resource_url}: {feed.bozo_exception}")
            return []

        return [self._parse_entry(entry, source.name) for entry in feed.entries]

    def get_source_name(self, url: str) -> str:
        """Generate name from RSS feed URL."""
        parsed = urlparse(url)
        domain = parsed.netloc.replace("www.", "")

        # Try to get feed title from the feed itself
        # But for now, use domain + path
        path = parsed.path.strip("/").replace("/", "-")
        if path and path not in ["rss", "feed", "atom", "index.xml"]:
            return f"{domain}-{path}"
        return domain

    def _parse_entry(self, entry, source_name: str) -> FeedItemIn:
        """Parse a single feed entry."""
        # Get basic fields with fallbacks
        title = getattr(entry, "title", "Untitled")
        link = getattr(entry, "link", "")
        local_id = getattr(entry, "id", link)

        # Get description/summary
        description = ""
        if hasattr(entry, "summary"):
            description = entry.summary
        elif hasattr(entry, "description"):
            description = entry.description
        elif hasattr(entry, "content") and entry.content:
            description = entry.content[0].get("value", "")

        published = self._parse_published_date(entry)

        return FeedItemIn(
            title=title,
            link=link,
            source_name=source_name,
            local_id=local_id,
            description=description,
            published=published,
            # RSS feeds typically don't have these
            points=0,
            views=0,
            num_comments=0,
            comments_url=None,
            article_url=link,
        )
