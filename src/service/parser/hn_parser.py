"""Hacker News RSS feed parser."""

from datetime import datetime

import feedparser
from bs4 import BeautifulSoup

from model.source import Source
from schemas import FeedItemIn
from service.parser.base import BaseParser, register_parser
from utils.logger import get_logger

logger = get_logger(__name__)


@register_parser("hackernews")
class HackerNewsParser(BaseParser):
    """Parser for Hacker News RSS feeds."""

    @classmethod
    def can_handle(cls, url: str) -> bool:
        """Check if URL is a Hacker News feed."""
        return "hnrss.org" in url or "news.ycombinator.com" in url

    def parse(self, source: Source) -> list[FeedItemIn]:
        """Parse Hacker News RSS feed."""
        feed = feedparser.parse(source.resource_url)
        return [self._parse_entry(item, source.name) for item in feed.entries]

    def get_source_name(self, url: str) -> str:
        """Generate name for HN feed."""
        # Extract feed type from URL (e.g., "frontpage", "newest", "best")
        path = url.split("/")[-1].split("?")[0] or "frontpage"
        return f"hackernews-{path}"

    def _parse_entry(self, item, source_name: str) -> FeedItemIn:
        """Parse a single feed entry."""
        local_id = item.id
        title = item.title
        published = datetime(*item.published_parsed[:6])
        comments = getattr(item, "comments", "")
        link = item.link
        summary = getattr(item, "summary", "")
        description = ""
        points = 0
        num_comments = 0
        article_url = ""

        try:
            soup = BeautifulSoup(summary, "html.parser")
            for p_tag in soup.find_all("p"):
                text = p_tag.text
                if text.startswith("Article URL:"):
                    article_url = text.split(": ")[1]
                elif text.startswith("Points:"):
                    points = int(text.split(": ")[1])
                elif text.startswith("# Comments:"):
                    num_comments = int(text.split(": ")[1])
                else:
                    description += text
        except Exception as ex:
            logger.error("Error while parsing feed item: %s", ex)

        return FeedItemIn(
            title=title,
            link=link,
            source_name=source_name,
            local_id=local_id,
            description=summary,
            points=points,
            comments_url=comments,
            article_url=article_url,
            num_comments=num_comments,
            published=published,
        )
