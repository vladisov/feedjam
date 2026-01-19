"""Reddit feed parser.

Parses Reddit RSS feeds for subreddits, users, and multi-reddits.
Extracts points and comment counts from the feed content.
"""

import re
from urllib.parse import urlparse

import feedparser
from bs4 import BeautifulSoup

from model.source import Source
from schemas import FeedItemIn
from service.parser.base import BaseParser, register_parser
from utils.logger import get_logger

logger = get_logger(__name__)

# Patterns for extracting data from Reddit RSS content
POINTS_PATTERN = re.compile(r"(\d+)\s*points?", re.IGNORECASE)
COMMENTS_PATTERN = re.compile(r"(\d+)\s*comments?", re.IGNORECASE)


@register_parser("reddit")
class RedditParser(BaseParser):
    """Parser for Reddit RSS feeds.

    Reddit provides RSS feeds for:
    - Subreddits: /r/{subreddit}/.rss
    - Users: /user/{username}/.rss
    - Multi-reddits: /user/{username}/m/{multi}/.rss
    - Search: /search.rss?q={query}
    """

    @classmethod
    def can_handle(cls, url: str) -> bool:
        """Check if URL is a valid Reddit feed URL."""
        lower_url = url.lower()

        # Must be a Reddit domain
        if "reddit.com" not in lower_url:
            return False

        # Check for valid Reddit feed patterns
        valid_patterns = [
            "/r/",  # Subreddit
            "/user/",  # User profile
            "/u/",  # User shorthand
            ".rss",  # Explicit RSS
            "/search",  # Search results
            "/top",  # Top posts
            "/new",  # New posts
            "/hot",  # Hot posts
            "/rising",  # Rising posts
        ]

        return any(pattern in lower_url for pattern in valid_patterns)

    def parse(self, source: Source) -> list[FeedItemIn]:
        """Parse Reddit RSS feed."""
        url = self._normalize_url(source.resource_url)
        logger.info(f"Fetching Reddit feed: {url}")

        feed = feedparser.parse(url)

        if feed.bozo and not feed.entries:
            logger.warning(f"Reddit feed parsing error for {url}: {feed.bozo_exception}")
            return []

        items = []
        for entry in feed.entries:
            try:
                item = self._parse_entry(entry, source.name)
                items.append(item)
            except Exception as e:
                logger.warning(f"Failed to parse Reddit entry: {e}")
                continue

        logger.info(f"Parsed {len(items)} items from Reddit: {source.name}")
        return items

    def get_source_name(self, url: str) -> str:
        """Generate name from Reddit URL."""
        parsed = urlparse(url)
        path_parts = [p for p in parsed.path.strip("/").split("/") if p and p != ".rss"]

        # Handle /r/subreddit format
        if len(path_parts) >= 2 and path_parts[0] == "r":
            subreddit = path_parts[1].replace(".rss", "")
            return f"reddit-r-{subreddit}"

        # Handle /user/username format
        if len(path_parts) >= 2 and path_parts[0] in ("user", "u"):
            username = path_parts[1].replace(".rss", "")
            return f"reddit-u-{username}"

        # Handle multi-reddit
        if len(path_parts) >= 4 and path_parts[2] == "m":
            return f"reddit-m-{path_parts[3]}"

        return "reddit"

    def _normalize_url(self, url: str) -> str:
        """Normalize URL to ensure it's an RSS feed URL."""
        # Remove trailing slashes
        url = url.rstrip("/")

        # If already an RSS URL, return as-is
        if url.endswith(".rss"):
            return url

        # If JSON URL, convert to RSS
        if url.endswith(".json"):
            return url.replace(".json", ".rss")

        # Add .rss extension
        return f"{url}/.rss"

    def _parse_entry(self, entry, source_name: str) -> FeedItemIn:
        """Parse a single Reddit entry."""
        title = getattr(entry, "title", "Untitled")
        link = getattr(entry, "link", "")
        local_id = getattr(entry, "id", link)

        # Reddit includes HTML content in the summary
        summary = getattr(entry, "summary", "") or getattr(entry, "content", [{}])[0].get(
            "value", ""
        )

        # Extract points and comments from the summary HTML
        points, num_comments, article_url, description = self._parse_content(summary)

        published = self._parse_published_date(entry)

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
            article_url=article_url or link,
        )

    def _parse_content(self, html_content: str) -> tuple[int, int, str | None, str]:
        """Parse Reddit RSS content to extract points, comments, article URL.

        Returns: (points, num_comments, article_url, description)
        """
        if not html_content:
            return 0, 0, None, ""

        points = 0
        num_comments = 0
        article_url = None
        description = ""

        try:
            soup = BeautifulSoup(html_content, "html.parser")

            # Get text content for description
            description = soup.get_text(separator=" ", strip=True)

            # Try to find points
            if match := POINTS_PATTERN.search(html_content):
                points = int(match.group(1))

            # Try to find comment count
            if match := COMMENTS_PATTERN.search(html_content):
                num_comments = int(match.group(1))

            # Try to find external article URL (for link posts)
            # Reddit RSS includes [link] tags for external URLs
            for link_tag in soup.find_all("a"):
                href = link_tag.get("href", "")
                text = link_tag.get_text(strip=True).lower()

                # Skip Reddit internal links
                if "reddit.com" in href:
                    continue

                # Look for [link] or external article links
                if text == "[link]" or (href and not href.startswith("#")):
                    article_url = href
                    break

        except Exception as e:
            logger.debug(f"Error parsing Reddit content: {e}")
            description = html_content

        return points, num_comments, article_url, description
