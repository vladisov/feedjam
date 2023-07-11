
from typing import Callable, List
from model.schema.feed_schema import FeedItemCreate, SourceBase, SourceSchema

from service.subscription.hn_parser import parse_hn_feed_item


def get_parser(source: SourceBase) -> Callable[[SourceSchema], List[FeedItemCreate]] | None:
    if source.name == 'hackernews':
        return parse_hn_feed_item
    return None
