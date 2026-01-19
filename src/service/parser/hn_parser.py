"""Hacker News RSS feed parser.

Parses Hacker News feeds from hnrss.org which provides structured RSS
with metadata like points, comments, and article URLs.
"""

import feedparser
from bs4 import BeautifulSoup

from model.source import Source
from schemas import FeedItemIn
from service.parser.base import BaseParser, register_parser
from utils.logger import get_logger

logger = get_logger(__name__)


@register_parser("hackernews")
class HackerNewsParser(BaseParser):
    """Parser for Hacker News RSS feeds.

    Supports feeds from:
    - hnrss.org (recommended, includes metadata)
    - news.ycombinator.com/rss
    """

    @classmethod
    def can_handle(cls, url: str) -> bool:
        """Check if URL is a Hacker News feed."""
        lower_url = url.lower()
        return "hnrss.org" in lower_url or "news.ycombinator.com" in lower_url

    def parse(self, source: Source) -> list[FeedItemIn]:
        """Parse Hacker News RSS feed."""
        logger.info(f"Fetching HN feed: {source.resource_url}")

        feed = feedparser.parse(source.resource_url)

        if feed.bozo and not feed.entries:
            logger.warning(f"HN feed parsing error: {feed.bozo_exception}")
            return []

        items = []
        for entry in feed.entries:
            try:
                item = self._parse_entry(entry, source.name)
                items.append(item)
            except Exception as e:
                logger.warning(f"Failed to parse HN entry '{getattr(entry, 'title', 'unknown')}': {e}")
                continue

        logger.info(f"Parsed {len(items)} items from HN: {source.name}")
        return items

    def get_source_name(self, url: str) -> str:
        """Generate name for HN feed."""
        # Extract feed type from URL (e.g., "frontpage", "newest", "best")
        path = url.split("/")[-1].split("?")[0]
        if not path or path == "rss":
            path = "frontpage"
        return f"hackernews-{path}"

    def _parse_entry(self, entry, source_name: str) -> FeedItemIn:
        """Parse a single HN feed entry."""
        local_id = getattr(entry, "id", "")
        title = getattr(entry, "title", "Untitled")
        link = getattr(entry, "link", "")
        comments_url = getattr(entry, "comments", "")
        summary = getattr(entry, "summary", "")

        # Parse published date safely
        published = self._parse_published_date(entry)

        # Extract metadata from hnrss.org summary HTML
        points, num_comments, article_url, description = self._parse_summary(summary)

        # Fallback: if no article_url found, use the link
        if not article_url:
            article_url = link

        return FeedItemIn(
            title=title,
            link=link,
            source_name=source_name,
            local_id=local_id,
            description=description or summary,
            points=points,
            comments_url=comments_url or link,
            article_url=article_url,
            num_comments=num_comments,
            published=published,
        )

    def _parse_summary(self, summary: str) -> tuple[int, int, str, str]:
        """Parse hnrss.org summary HTML to extract metadata.

        The summary format from hnrss.org:
        <p>Article URL: https://...</p>
        <p>Points: 123</p>
        <p># Comments: 45</p>

        Returns: (points, num_comments, article_url, description)
        """
        if not summary:
            return 0, 0, "", ""

        points = 0
        num_comments = 0
        article_url = ""
        description_parts = []

        try:
            soup = BeautifulSoup(summary, "html.parser")

            for p_tag in soup.find_all("p"):
                text = p_tag.get_text(strip=True)

                if text.startswith("Article URL:"):
                    # Extract URL after the colon
                    parts = text.split(": ", 1)
                    if len(parts) > 1:
                        article_url = parts[1].strip()

                elif text.startswith("Points:"):
                    try:
                        points = int(text.split(": ", 1)[1].strip())
                    except (ValueError, IndexError):
                        pass

                elif text.startswith("# Comments:"):
                    try:
                        num_comments = int(text.split(": ", 1)[1].strip())
                    except (ValueError, IndexError):
                        pass

                else:
                    # Regular content paragraph
                    if text:
                        description_parts.append(text)

        except Exception as e:
            logger.debug(f"Error parsing HN summary: {e}")
            return 0, 0, "", summary

        description = " ".join(description_parts)
        return points, num_comments, article_url, description
