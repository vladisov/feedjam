"""Reddit feed parser.

Parses Reddit JSON API for subreddits, users, and multi-reddits.
Uses JSON API instead of RSS to get upvotes and comment counts.
"""

from datetime import UTC, datetime
from urllib.parse import urlparse

import requests

from model.source import Source
from schemas import FeedItemIn
from service.parser.base import BaseParser, register_parser
from utils.logger import get_logger

logger = get_logger(__name__)

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; FeedJam/1.0; +https://feedjam.app)"}


@register_parser("reddit")
class RedditParser(BaseParser):
    """Parser for Reddit feeds using JSON API.

    Reddit provides JSON endpoints for:
    - Subreddits: /r/{subreddit}.json
    - Users: /user/{username}.json
    - Multi-reddits: /user/{username}/m/{multi}.json
    - Search: /search.json?q={query}
    """

    VALID_PATH_PATTERNS = (
        "/r/",
        "/user/",
        "/u/",
        ".json",
        ".rss",
        "/search",
        "/top",
        "/new",
        "/hot",
        "/rising",
    )

    @classmethod
    def can_handle(cls, url: str) -> bool:
        """Check if URL is a valid Reddit feed URL."""
        lower_url = url.lower()

        if "reddit.com" not in lower_url:
            return False

        return any(pattern in lower_url for pattern in cls.VALID_PATH_PATTERNS)

    def parse(self, source: Source) -> list[FeedItemIn]:
        """Parse Reddit JSON feed."""
        url = self._normalize_url(source.resource_url)
        logger.info(f"Fetching Reddit feed: {url}")

        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            logger.warning(f"Reddit API request failed for {url}: {e}")
            return []
        except ValueError as e:
            logger.warning(f"Reddit API returned invalid JSON for {url}: {e}")
            return []

        # Handle different response formats
        posts = self._extract_posts(data)
        if not posts:
            logger.warning(f"No posts found in Reddit response for {url}")
            return []

        items = []
        for post in posts:
            try:
                item = self._parse_post(post, source.name)
                items.append(item)
            except Exception as e:
                logger.warning(f"Failed to parse Reddit post: {e}")
                continue

        logger.info(f"Parsed {len(items)} items from Reddit: {source.name}")
        return items

    def get_source_name(self, url: str) -> str:
        """Generate name from Reddit URL."""
        parsed = urlparse(url)
        path_parts = [
            p.replace(".json", "").replace(".rss", "")
            for p in parsed.path.strip("/").split("/")
            if p and p not in (".json", ".rss")
        ]

        if len(path_parts) < 2:
            return "reddit"

        prefix = path_parts[0]
        name = path_parts[1]

        if prefix == "r":
            return f"reddit-r-{name}"

        if prefix in ("user", "u"):
            return f"reddit-u-{name}"

        if len(path_parts) >= 4 and path_parts[2] == "m":
            return f"reddit-m-{path_parts[3]}"

        return "reddit"

    def _normalize_url(self, url: str) -> str:
        """Normalize URL to JSON API endpoint."""
        url = url.rstrip("/")

        # Remove .rss extension if present
        if url.endswith(".rss"):
            url = url[:-4]

        # Add .json extension if not present
        if not url.endswith(".json"):
            url = f"{url}.json"

        return url

    def _extract_posts(self, data: dict) -> list[dict]:
        """Extract posts from Reddit API response."""
        # Standard listing response
        if "data" in data and "children" in data["data"]:
            return [child["data"] for child in data["data"]["children"]]

        # Search or other format
        if isinstance(data, list) and len(data) > 0:
            if "data" in data[0] and "children" in data[0]["data"]:
                return [child["data"] for child in data[0]["data"]["children"]]

        return []

    def _parse_post(self, post: dict, source_name: str) -> FeedItemIn:
        """Parse a single Reddit post from JSON."""
        permalink = post.get("permalink", "")
        post_id = post.get("id", "")
        link = f"https://www.reddit.com{permalink}" if permalink else ""

        # For self-posts, use Reddit link; for link posts, use external URL
        is_self = post.get("is_self", False)
        article_url = link if is_self else post.get("url", "")

        # Parse timestamp
        created_utc = post.get("created_utc", 0)
        published = datetime.fromtimestamp(created_utc, tz=UTC) if created_utc else None

        # Truncate selftext to reasonable length
        selftext = post.get("selftext") or ""

        return FeedItemIn(
            title=post.get("title", "Untitled"),
            link=link,
            source_name=source_name,
            local_id=f"t3_{post_id}" if post_id else link,
            description=selftext[:2000],
            published=published,
            points=post.get("score", 0) or post.get("ups", 0),
            views=0,
            num_comments=post.get("num_comments", 0),
            comments_url=link,
            article_url=article_url,
        )
