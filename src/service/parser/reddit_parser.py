"""Reddit feed parser."""

from urllib.parse import urlparse

import feedparser

from model.source import Source
from schemas import FeedItemIn
from service.parser.base import BaseParser, register_parser
from utils.logger import get_logger

logger = get_logger(__name__)


@register_parser("reddit")
class RedditParser(BaseParser):
    """Parser for Reddit RSS feeds.

    Reddit provides RSS feeds for subreddits, users, and search results.
    Format: https://www.reddit.com/r/{subreddit}/.rss
    """

    @classmethod
    def can_handle(cls, url: str) -> bool:
        """Check if URL is a Reddit feed."""
        return "reddit.com" in url

    def parse(self, source: Source) -> list[FeedItemIn]:
        """Parse Reddit RSS feed."""
        # Ensure URL ends with .rss for Reddit
        url = source.resource_url
        if not url.endswith(".rss") and not url.endswith(".json"):
            url = url.rstrip("/") + "/.rss"

        feed = feedparser.parse(url)

        if feed.bozo and not feed.entries:
            logger.warning(f"Feed parsing error for {url}: {feed.bozo_exception}")
            return []

        return [self._parse_entry(entry, source.name) for entry in feed.entries]

    def get_source_name(self, url: str) -> str:
        """Generate name from Reddit URL."""
        parsed = urlparse(url)
        path_parts = parsed.path.strip("/").split("/")

        # Handle /r/subreddit format
        if len(path_parts) >= 2 and path_parts[0] == "r":
            return f"reddit-r-{path_parts[1]}"

        # Handle /user/username format
        if len(path_parts) >= 2 and path_parts[0] in ("user", "u"):
            return f"reddit-u-{path_parts[1]}"

        return "reddit"

    def _parse_entry(self, entry, source_name: str) -> FeedItemIn:
        """Parse a single Reddit entry."""
        title = getattr(entry, "title", "Untitled")
        link = getattr(entry, "link", "")
        local_id = getattr(entry, "id", link)

        # Reddit includes HTML content in the summary
        description = ""
        if hasattr(entry, "summary"):
            description = entry.summary

        published = self._parse_published_date(entry)

        # Extract score/points from title if available (Reddit format: "[score] title")
        points = 0
        num_comments = 0

        return FeedItemIn(
            title=title,
            link=link,
            source_name=source_name,
            local_id=local_id,
            description=description,
            published=published,
            points=points,
            views=0,
            num_comments=num_comments,
            comments_url=link,  # Reddit post URL is also the comments URL
            article_url=link,
        )
