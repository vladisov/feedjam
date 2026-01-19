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
    try:
        if "K" in views_str:
            return int(float(views_str.replace("K", "")) * 1000)
        if "M" in views_str:
            return int(float(views_str.replace("M", "")) * 1000000)
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

        logger.info(f"Parsed {len(feed_items)} items from Telegram channel: {source.name}")
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
        items = []

        # Find all message containers - try multiple selectors for robustness
        selectors = [
            {"class_": "tgme_widget_message_wrap"},
            {"class_": "tgme_widget_message"},
            {"attrs": {"data-post": True}},
        ]

        messages = []
        for selector in selectors:
            messages = soup.find_all("div", **selector)
            if messages:
                break

        for message in messages:
            item = self._extract_message_data(message)
            if item:
                items.append(item)

        return items

    def _extract_message_data(self, message) -> dict | None:
        """Extract data from a single message element."""
        item = {}

        # Extract message text - try multiple selectors
        text_selectors = [
            "tgme_widget_message_text",
            "message_text",
        ]

        for selector in text_selectors:
            text_div = message.find("div", class_=selector)
            if text_div:
                # Get text content, preserving some structure
                item["message"] = text_div.get_text(separator="\n", strip=True)
                break

        # Extract post link
        link_elem = message.find("a", class_="tgme_widget_message_date")
        if link_elem and link_elem.get("href"):
            item["post_link"] = link_elem["href"]
        else:
            # Try data-post attribute
            post_id = message.get("data-post")
            if post_id:
                item["post_link"] = f"https://t.me/{post_id}"

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

    def _create_feed_item(self, item: dict, source: Source) -> FeedItemIn:
        """Create FeedItemIn from parsed message data."""
        message = item.get("message", "")
        link = item.get("post_link", "")
        views = parse_view_count(item.get("views", ""))

        # Parse datetime
        published = None
        if item.get("datetime"):
            try:
                published = date_parser.parse(item["datetime"])
            except (ValueError, TypeError):
                pass

        # Use first line as title, rest as description
        lines = message.split("\n", 1)
        title = lines[0][:300] if lines else ""  # Cap title length
        description = message

        return FeedItemIn(
            title=title,
            link=link,
            description=description,
            source_name=source.name,
            views=views,
            comments_url=None,
            article_url=link,
            num_comments=0,
            local_id=link,
            published=published,
        )
