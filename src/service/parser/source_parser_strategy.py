
from typing import Callable, List
from model.schema.feed_schema import FeedItemCreate, SourceBase, SourceSchema

from service.parser.hn_parser import parse_hn_feed
from service.parser.telegram_parser import parse_telegram_feed


def get_parser(source: SourceBase) -> Callable[[SourceSchema], List[FeedItemCreate]] | None:
    if 'hackernews' in source.name:
        return parse_hn_feed
    if 'telegram' in source.name or "t.me" in source.resource_url:
        return parse_telegram_feed
    return None


def parse_name(resource_url: str) -> str:
    if 'hackernews' in resource_url or 'hn' in resource_url:
        return 'hackernews-'+resource_url.split('/')[-1]
    return resource_url
