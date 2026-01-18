"""GitHub feed parser."""

from datetime import datetime
from urllib.parse import urlparse

import feedparser

from model.source import Source
from schemas import FeedItemIn
from service.parser.base import BaseParser, register_parser
from utils.logger import get_logger

logger = get_logger(__name__)


@register_parser("github")
class GitHubParser(BaseParser):
    """Parser for GitHub RSS/Atom feeds.

    GitHub provides Atom feeds for:
    - Repository releases: https://github.com/{owner}/{repo}/releases.atom
    - Repository commits: https://github.com/{owner}/{repo}/commits.atom
    - Repository tags: https://github.com/{owner}/{repo}/tags.atom
    - User activity: https://github.com/{user}.atom
    """

    @classmethod
    def can_handle(cls, url: str) -> bool:
        """Check if URL is a GitHub feed."""
        return "github.com" in url

    def parse(self, source: Source) -> list[FeedItemIn]:
        """Parse GitHub Atom feed."""
        url = self._normalize_url(source.resource_url)
        feed = feedparser.parse(url)

        if feed.bozo and not feed.entries:
            logger.warning(f"Feed parsing error for {url}: {feed.bozo_exception}")
            return []

        return [self._parse_entry(entry, source.name) for entry in feed.entries]

    def get_source_name(self, url: str) -> str:
        """Generate name from GitHub URL."""
        parsed = urlparse(url)
        path_parts = [p for p in parsed.path.strip("/").split("/") if p]

        # Remove .atom extension if present
        if path_parts and path_parts[-1].endswith(".atom"):
            path_parts[-1] = path_parts[-1].replace(".atom", "")

        # Handle {owner}/{repo}/releases or commits
        if len(path_parts) >= 2:
            owner = path_parts[0]
            repo = path_parts[1]
            feed_type = path_parts[2] if len(path_parts) > 2 else "activity"
            return f"github-{owner}-{repo}-{feed_type}"

        # Handle user activity feed
        if len(path_parts) == 1:
            return f"github-{path_parts[0]}"

        return "github"

    def _normalize_url(self, url: str) -> str:
        """Ensure URL ends with .atom for GitHub feeds."""
        # Already has .atom extension
        if url.endswith(".atom"):
            return url

        # Add .atom for common GitHub URLs
        url = url.rstrip("/")

        # Check if it's a releases/commits/tags page
        if any(x in url for x in ["/releases", "/commits", "/tags"]):
            return f"{url}.atom"

        # For user URLs (github.com/username), add .atom
        parsed = urlparse(url)
        path_parts = [p for p in parsed.path.strip("/").split("/") if p]
        if len(path_parts) == 1:
            return f"{url}.atom"

        # For repo URLs, default to releases feed
        if len(path_parts) == 2:
            return f"{url}/releases.atom"

        return url

    def _parse_entry(self, entry, source_name: str) -> FeedItemIn:
        """Parse a single GitHub entry."""
        title = getattr(entry, "title", "Untitled")
        link = getattr(entry, "link", "")
        local_id = getattr(entry, "id", link)

        # GitHub Atom feeds include content
        description = ""
        if hasattr(entry, "content") and entry.content:
            description = entry.content[0].get("value", "")
        elif hasattr(entry, "summary"):
            description = entry.summary

        # Parse updated/published date
        published = None
        if hasattr(entry, "updated_parsed") and entry.updated_parsed:
            try:
                published = datetime(*entry.updated_parsed[:6])
            except (TypeError, ValueError):
                pass
        elif hasattr(entry, "published_parsed") and entry.published_parsed:
            try:
                published = datetime(*entry.published_parsed[:6])
            except (TypeError, ValueError):
                pass

        if not published:
            published = datetime.now()

        return FeedItemIn(
            title=title,
            link=link,
            source_name=source_name,
            local_id=local_id,
            description=description,
            published=published,
            points=0,
            views=0,
            num_comments=0,
            comments_url=link,
            article_url=link,
        )
