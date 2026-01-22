"""Telegram channel parser.

Parses Telegram public channels using the /s/ (preview) embed page format.
This is more stable than the widget page as it's designed for embedding.
"""

import time
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from dateutil import parser as date_parser

from model.source import Source
from schemas import FeedItemIn
from service.parser.base import BaseParser, register_parser
from utils.logger import get_logger

logger = get_logger(__name__)

# Request settings
REQUEST_TIMEOUT = 30
MAX_RETRIES = 2
RETRY_DELAY = 1


def parse_view_count(views_str: str) -> int:
    """Parse view count string like '1.5K' or '2.3M' to integer."""
    if not views_str:
        return 0

    views_str = views_str.strip().upper()
    multipliers = {"K": 1_000, "M": 1_000_000}

    try:
        for suffix, multiplier in multipliers.items():
            if suffix in views_str:
                return int(float(views_str.replace(suffix, "")) * multiplier)
        return int(views_str.replace(",", "").replace(" ", ""))
    except (ValueError, AttributeError):
        return 0


@register_parser("telegram")
class TelegramParser(BaseParser):
    """Parser for Telegram public channels.

    Uses the /s/ embed page format which is more stable than the widget page.
    Handles both t.me and telegram.me URLs.
    """

    @classmethod
    def can_handle(cls, url: str) -> bool:
        """Check if URL is a Telegram channel."""
        lower_url = url.lower()
        return "t.me/" in lower_url or "telegram.me/" in lower_url

    def parse(self, source: Source) -> list[FeedItemIn]:
        """Parse a Telegram channel's public page."""
        url = self._normalize_url(source.resource_url)
        logger.info(f"Parsing Telegram channel: {url}")
        html = self._fetch_with_retry(url)

        if not html:
            logger.error(f"Failed to fetch Telegram channel: {source.resource_url}")
            return []

        items = self._parse_html(html)
        feed_items = []

        for item in items:
            try:
                feed_item = self._create_feed_item(item, source)
                if feed_item.title:  # Skip empty messages
                    feed_items.append(feed_item)
            except Exception as e:
                logger.warning(f"Failed to parse Telegram message: {e}")
                continue

        logger.info(f"Parsed {len(feed_items)} items from Telegram: {source.name}")
        return feed_items

    def get_source_name(self, url: str) -> str:
        """Generate name for Telegram channel."""
        channel = self._extract_channel_name(url)
        return f"telegram-{channel}" if channel else "telegram"

    def _normalize_url(self, url: str) -> str:
        """Normalize URL to use /s/ embed format."""
        channel = self._extract_channel_name(url)

        if not channel:
            return url

        # Use /s/ format for stable scraping
        return f"https://t.me/s/{channel}"

    def _extract_channel_name(self, url: str) -> str | None:
        """Extract channel name from URL."""
        parsed = urlparse(url)
        path = parsed.path.strip("/")

        # Handle /s/channel format
        if path.startswith("s/"):
            path = path[2:]

        # Get first path segment (channel name)
        parts = path.split("/")
        if parts and parts[0]:
            # Filter out message IDs (numeric)
            channel = parts[0]
            if not channel.isdigit():
                return channel

        return None

    def _fetch_with_retry(self, url: str) -> str | None:
        """Fetch URL with retry logic."""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }

        for attempt in range(MAX_RETRIES + 1):
            try:
                response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
                response.raise_for_status()
                return response.text
            except requests.RequestException as e:
                logger.warning(f"Telegram fetch attempt {attempt + 1} failed: {e}")
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY * (attempt + 1))

        return None

    def _parse_html(self, html: str) -> list[dict]:
        """Parse Telegram channel HTML and extract messages."""
        soup = BeautifulSoup(html, "html.parser")
        messages = self._find_messages(soup)

        items = []
        for message in messages:
            item = self._extract_message_data(message)
            if item:
                items.append(item)
        return items

    def _find_messages(self, soup: BeautifulSoup) -> list:
        """Find message containers using multiple selectors for robustness."""
        selectors = [
            {"class_": "tgme_widget_message_wrap"},
            {"class_": "tgme_widget_message"},
            {"attrs": {"data-post": True}},
        ]
        for selector in selectors:
            messages = soup.find_all("div", **selector)
            if messages:
                return messages
        return []

    def _extract_message_data(self, message) -> dict | None:
        """Extract data from a single message element."""
        item = {}

        # Extract message text
        item["message"] = self._extract_text(message)

        # Extract post link
        item["post_link"] = self._extract_post_link(message)

        # Extract datetime
        time_elem = message.find("time")
        if time_elem:
            item["datetime"] = time_elem.get("datetime")

        # Extract view count
        views_elem = message.find("span", class_="tgme_widget_message_views")
        if views_elem:
            item["views"] = views_elem.get_text(strip=True)

        # Only return if we have essential data
        if item.get("message") or item.get("post_link"):
            return item
        return None

    def _extract_text(self, message) -> str | None:
        """Extract message text from various possible selectors."""
        for class_name in ("tgme_widget_message_text", "message_text"):
            text_div = message.find("div", class_=class_name)
            if text_div:
                return text_div.get_text(separator="\n", strip=True)
        return None

    def _extract_post_link(self, message) -> str | None:
        """Extract post link from message element."""
        link_elem = message.find("a", class_="tgme_widget_message_date")
        if link_elem and link_elem.get("href"):
            return link_elem["href"]

        post_id = message.get("data-post")
        if post_id:
            return f"https://t.me/{post_id}"
        return None

    def _create_feed_item(self, item: dict, source: Source) -> FeedItemIn:
        """Create FeedItemIn from parsed message data."""
        message = item.get("message", "")
        link = item.get("post_link", "")
        views = parse_view_count(item.get("views", ""))
        published = self._parse_datetime(item.get("datetime"))

        # Use first line as title (capped at 300 chars), full message as description
        first_line = message.split("\n", 1)[0]
        title = first_line[:300]

        return FeedItemIn(
            title=title,
            link=link,
            description=message,
            source_name=source.name,
            views=views,
            comments_url=None,
            article_url=link,
            num_comments=0,
            local_id=link,
            published=published,
        )

    def _parse_datetime(self, datetime_str: str | None):
        """Parse datetime string, returning None on failure."""
        if not datetime_str:
            return None
        try:
            return date_parser.parse(datetime_str)
        except (ValueError, TypeError):
            return None
