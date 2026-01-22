"""YouTube feed parser."""

from urllib.parse import parse_qs, urlparse

import feedparser

from model.source import Source
from schemas import FeedItemIn
from service.parser.base import BaseParser, register_parser
from utils.logger import get_logger

logger = get_logger(__name__)


@register_parser("youtube")
class YouTubeParser(BaseParser):
    """Parser for YouTube RSS feeds.

    YouTube provides RSS feeds for channels and playlists.
    Channel: https://www.youtube.com/feeds/videos.xml?channel_id={id}
    Playlist: https://www.youtube.com/feeds/videos.xml?playlist_id={id}
    """

    YOUTUBE_FEED_BASE = "https://www.youtube.com/feeds/videos.xml"

    @classmethod
    def can_handle(cls, url: str) -> bool:
        """Check if URL is a YouTube feed or channel."""
        return "youtube.com" in url or "youtu.be" in url or "youtube.com/feeds/videos.xml" in url

    def parse(self, source: Source) -> list[FeedItemIn]:
        """Parse YouTube RSS feed."""
        url = self._normalize_url(source.resource_url)
        logger.info(f"Parsing YouTube feed: {url}")
        feed = feedparser.parse(url)

        if feed.bozo and not feed.entries:
            logger.warning(f"Feed parsing error for {url}: {feed.bozo_exception}")
            return []

        items = [self._parse_entry(entry, source.name) for entry in feed.entries]
        logger.info(f"Parsed {len(items)} items from YouTube: {source.name}")
        return items

    def get_source_name(self, url: str) -> str:
        """Generate name from YouTube URL."""
        parsed = urlparse(url)

        # Handle channel URLs
        if "/channel/" in url:
            path_parts = parsed.path.split("/")
            for i, part in enumerate(path_parts):
                if part == "channel" and i + 1 < len(path_parts):
                    return f"youtube-{path_parts[i + 1][:12]}"

        # Handle @username URLs
        if "/@" in url:
            path_parts = parsed.path.split("/")
            for part in path_parts:
                if part.startswith("@"):
                    return f"youtube-{part[1:]}"

        # Handle feed URLs with channel_id
        if "channel_id=" in url:
            qs = parse_qs(parsed.query)
            if "channel_id" in qs:
                return f"youtube-{qs['channel_id'][0][:12]}"

        return "youtube"

    def _normalize_url(self, url: str) -> str:
        """Convert various YouTube URLs to RSS feed URL."""
        # Already a feed URL
        if "feeds/videos.xml" in url:
            return url

        parsed = urlparse(url)

        # Handle /channel/{id} format
        if "/channel/" in url:
            path_parts = parsed.path.split("/")
            for i, part in enumerate(path_parts):
                if part == "channel" and i + 1 < len(path_parts):
                    channel_id = path_parts[i + 1]
                    return f"{self.YOUTUBE_FEED_BASE}?channel_id={channel_id}"

        # For other URLs, return as-is and let feedparser handle it
        return url

    def _parse_entry(self, entry, source_name: str) -> FeedItemIn:
        """Parse a single YouTube entry."""
        title = getattr(entry, "title", "Untitled")
        link = getattr(entry, "link", "")
        local_id = getattr(entry, "yt_videoid", "") or getattr(entry, "id", link)

        # YouTube feeds include media description
        description = ""
        if hasattr(entry, "summary"):
            description = entry.summary
        elif hasattr(entry, "media_description"):
            description = entry.media_description

        published = self._parse_published_date(entry)

        # YouTube-specific: views from media statistics
        views = 0
        if hasattr(entry, "media_statistics"):
            try:
                views = int(entry.media_statistics.get("views", 0))
            except (ValueError, AttributeError):
                pass

        return FeedItemIn(
            title=title,
            link=link,
            source_name=source_name,
            local_id=local_id,
            description=description,
            published=published,
            points=0,
            views=views,
            num_comments=0,
            comments_url=link,
            article_url=link,
        )
