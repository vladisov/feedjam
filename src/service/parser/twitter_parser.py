"""Twitter/X parser via Nitter RSS feeds.

Twitter API v2 requires paid access ($100/month), so we use Nitter instances
which provide RSS feeds for public Twitter accounts.

Supported URL formats:
- twitter.com/username
- x.com/username
- nitter.net/username/rss (direct Nitter RSS)
- Any Nitter instance URL
"""

from urllib.parse import urlparse

import feedparser

from model.source import Source
from schemas import FeedItemIn
from service.parser.base import BaseParser, register_parser
from utils.logger import get_logger

logger = get_logger(__name__)

# List of known Nitter instances (can be expanded)
# See https://github.com/zedeus/nitter/wiki/Instances for more
NITTER_INSTANCES = [
    "nitter.net",
    "nitter.privacydev.net",
    "nitter.poast.org",
    "nitter.1d4.us",
]

# Default Nitter instance to use for converting Twitter URLs
DEFAULT_NITTER_INSTANCE = "nitter.privacydev.net"


@register_parser("twitter")
class TwitterParser(BaseParser):
    """Parser for Twitter/X via Nitter RSS feeds.

    Converts Twitter/X URLs to Nitter RSS feeds for parsing.
    Also supports direct Nitter RSS URLs.
    """

    @classmethod
    def can_handle(cls, url: str) -> bool:
        """Check if URL is a Twitter/X or Nitter URL."""
        lower_url = url.lower()

        # Twitter/X URLs
        if "twitter.com/" in lower_url or "x.com/" in lower_url:
            return True

        # Nitter instance URLs
        for instance in NITTER_INSTANCES:
            if instance in lower_url:
                return True

        # Generic nitter detection
        if "nitter" in lower_url:
            return True

        return False

    def parse(self, source: Source) -> list[FeedItemIn]:
        """Parse Twitter feed via Nitter RSS."""
        rss_url = self._get_nitter_rss_url(source.resource_url)
        logger.info(f"Fetching Twitter feed via Nitter: {rss_url}")

        feed = feedparser.parse(rss_url)

        if feed.bozo and not feed.entries:
            logger.warning(f"Feed parsing error for {rss_url}: {feed.bozo_exception}")
            # Try alternate Nitter instance
            for instance in NITTER_INSTANCES:
                if instance not in rss_url:
                    alt_url = self._convert_to_nitter_rss(source.resource_url, instance)
                    logger.info(f"Trying alternate Nitter instance: {alt_url}")
                    feed = feedparser.parse(alt_url)
                    if feed.entries:
                        break

        if not feed.entries:
            logger.warning(f"No entries found for Twitter feed: {source.resource_url}")
            return []

        items = []
        for entry in feed.entries:
            try:
                item = self._parse_entry(entry, source.name)
                items.append(item)
            except Exception as e:
                logger.warning(f"Failed to parse Twitter entry: {e}")
                continue

        return items

    def get_source_name(self, url: str) -> str:
        """Generate name from Twitter URL."""
        username = self._extract_username(url)
        return f"twitter-{username}" if username else "twitter"

    def _get_nitter_rss_url(self, url: str) -> str:
        """Convert any Twitter/Nitter URL to Nitter RSS URL."""
        parsed = urlparse(url)
        host = parsed.netloc.lower()

        # Already a Nitter RSS URL
        if "/rss" in url:
            return url

        # Already on a Nitter instance, just add /rss
        for instance in NITTER_INSTANCES:
            if instance in host or "nitter" in host:
                path = parsed.path.rstrip("/")
                return f"https://{parsed.netloc}{path}/rss"

        # Twitter/X URL - convert to Nitter
        return self._convert_to_nitter_rss(url, DEFAULT_NITTER_INSTANCE)

    def _convert_to_nitter_rss(self, url: str, nitter_instance: str) -> str:
        """Convert Twitter URL to Nitter RSS URL."""
        username = self._extract_username(url)
        if username:
            return f"https://{nitter_instance}/{username}/rss"
        return url

    def _extract_username(self, url: str) -> str | None:
        """Extract username from Twitter/Nitter URL."""
        parsed = urlparse(url)
        path_parts = parsed.path.strip("/").split("/")

        if path_parts and path_parts[0]:
            # Filter out known non-username paths
            username = path_parts[0].lower()
            if username not in ("search", "explore", "home", "i", "intent", "rss"):
                return path_parts[0]

        return None

    def _parse_entry(self, entry, source_name: str) -> FeedItemIn:
        """Parse a single Nitter RSS entry."""
        title = getattr(entry, "title", "")
        link = getattr(entry, "link", "")
        local_id = getattr(entry, "id", link)
        description = getattr(entry, "description", "") or getattr(entry, "summary", "")

        # Convert Nitter link back to Twitter for the article URL
        article_url = link
        if "nitter" in link.lower():
            article_url = self._nitter_to_twitter_url(link)

        published = self._parse_published_date(entry)

        # Nitter doesn't provide engagement metrics in RSS
        # Would need to scrape the page for likes/retweets

        return FeedItemIn(
            title=title[:500] if len(title) > 500 else title,  # Truncate long tweets
            link=link,
            source_name=source_name,
            local_id=local_id,
            description=description,
            published=published,
            points=0,  # No like count in RSS
            views=0,
            num_comments=0,  # No reply count in RSS
            comments_url=article_url,
            article_url=article_url,
        )

    def _nitter_to_twitter_url(self, nitter_url: str) -> str:
        """Convert Nitter URL back to Twitter URL."""
        parsed = urlparse(nitter_url)
        return f"https://twitter.com{parsed.path}"
