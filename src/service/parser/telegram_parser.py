"""Telegram channel parser."""

import html2text
import requests
from bs4 import BeautifulSoup
from dateutil import parser

from model.source import Source
from schemas import FeedItemIn
from service.parser.base import BaseParser, register_parser
from utils.logger import get_logger
from utils.utils import parse_format

logger = get_logger(__name__)


@register_parser("telegram")
class TelegramParser(BaseParser):
    """Parser for Telegram public channels."""

    @classmethod
    def can_handle(cls, url: str) -> bool:
        """Check if URL is a Telegram channel."""
        return "t.me/" in url or "telegram.me/" in url

    def parse(self, source: Source) -> list[FeedItemIn]:
        """Parse a Telegram channel's public page."""
        items = self._fetch_telegram_items(source.resource_url)
        feed_items = []
        for item in items:
            try:
                feed_item = self._parse_item(item, source)
                feed_items.append(feed_item)
            except Exception as ex:
                logger.error(f"Error while parsing feed item: {ex}")
        return feed_items

    def get_source_name(self, url: str) -> str:
        """Generate name for Telegram channel."""
        # Extract channel name from URL (e.g., t.me/channel_name)
        channel = url.rstrip("/").split("/")[-1]
        return f"telegram-{channel}"

    def _parse_item(self, item: dict, source: Source) -> FeedItemIn:
        """Parse a single Telegram message."""
        title = item.get("message", "")
        link = item.get("post_link", "")
        views_str = item.get("views", "0")
        views = parse_format(views_str)
        published = item.get("datetime", "")
        if published:
            published = parser.parse(published)

        return FeedItemIn(
            title=title,
            link=link,
            description=title,
            source_name=source.name,
            views=views,
            comments_url=None,
            article_url=link,
            num_comments=0,
            local_id=link,
            published=published,
        )

    def _fetch_telegram_items(self, url: str) -> list[dict]:
        """Fetch and parse Telegram channel HTML."""
        res = requests.get(url, timeout=30)
        soup = BeautifulSoup(res.text, "html.parser")
        messages = soup.find_all(
            "div", class_="tgme_widget_message text_not_supported_wrap js-widget_message"
        )

        items = []
        for message in messages:
            item = {}

            # Extract main message
            if text_div := message.find("div", class_="tgme_widget_message_text"):
                item["message"] = html2text.html2text(text_div.text)

            # Extract metadata
            if meta_div := message.find("div", class_="tgme_widget_message_info short js-message_info"):
                if views := meta_div.find("span", class_="tgme_widget_message_views"):
                    item["views"] = views.text
                if date_time := meta_div.find("time", class_="time"):
                    item["datetime"] = date_time["datetime"]
                if post_link := meta_div.find("a", class_="tgme_widget_message_date"):
                    item["post_link"] = post_link["href"]

            items.append(item)

        return items
