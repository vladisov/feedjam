"""Telegram channel parser."""

import html2text
import requests
from bs4 import BeautifulSoup
from dateutil import parser

from model.source import Source
from schemas import FeedItemIn
from utils.logger import get_logger
from utils.utils import parse_format

logger = get_logger(__name__)


def parse_telegram_feed(source: Source) -> list[FeedItemIn]:
    """Parse a Telegram channel's public page."""
    items = _fetch_telegram_items(source.resource_url)
    feed_items = []
    for item in items:
        try:
            feed_item = _parse_item(item, source)
            feed_items.append(feed_item)
        except Exception as ex:
            logger.error(f"Error while parsing feed item: {ex}")
    return feed_items


def _parse_item(item: dict, source: Source) -> FeedItemIn:
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


def _fetch_telegram_items(url: str) -> list[dict]:
    """Fetch and parse Telegram channel HTML."""
    res = requests.get(url)
    soup = BeautifulSoup(res.text, "html.parser")
    messages = soup.find_all(
        "div", class_="tgme_widget_message text_not_supported_wrap js-widget_message"
    )

    items = []
    for message in messages:
        item = {}

        # Extract main message
        text_div = message.find("div", class_="tgme_widget_message_text")
        if text_div is not None:
            item["message"] = html2text.html2text(text_div.text)

        # Extract metadata
        meta_div = message.find("div", class_="tgme_widget_message_info short js-message_info")
        if meta_div is not None:
            views = meta_div.find("span", class_="tgme_widget_message_views")
            if views is not None:
                item["views"] = views.text

            date_time = meta_div.find("time", class_="time")
            if date_time is not None:
                item["datetime"] = date_time["datetime"]

            post_link = meta_div.find("a", class_="tgme_widget_message_date")
            if post_link is not None:
                item["post_link"] = post_link["href"]

        items.append(item)

    return items
