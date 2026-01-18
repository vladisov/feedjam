"""Source parser strategy - selects appropriate parser for a source."""

from collections.abc import Callable

from model.source import Source
from schemas import FeedItemIn
from service.parser.hn_parser import parse_hn_feed
from service.parser.telegram_parser import parse_telegram_feed

ParserFunc = Callable[[Source], list[FeedItemIn]]


def get_parser(source: Source) -> ParserFunc | None:
    """Get the appropriate parser for a source."""
    if "hackernews" in source.name:
        return parse_hn_feed
    if "telegram" in source.name or "t.me" in source.resource_url:
        return parse_telegram_feed
    return None


def parse_name(resource_url: str) -> str:
    """Parse source name from URL."""
    if "hackernews" in resource_url or "hn" in resource_url:
        return "hackernews-" + resource_url.split("/")[-1]
    if "t.me" in resource_url:
        return "telegram-" + resource_url.split("/")[-1]
    return resource_url
