from datetime import datetime
from typing import List
from bs4 import BeautifulSoup
import feedparser
from model.schema.feed_schema import FeedItemCreate, SourceSchema
from utils.logger import get_logger

logger = get_logger(__name__)


def parse_hn_feed(source: SourceSchema) -> List[FeedItemCreate]:
    feed = feedparser.parse(source.resource_url)
    return [_crete_hn_feed_item(item, source.name) for item in feed.entries]


def _crete_hn_feed_item(item, source_name: str) -> FeedItemCreate:
    local_id = item.id
    title = item.title
    published = datetime(*item.published_parsed[:6])
    comments = item.comments
    link = item.link
    summary = item.summary
    description = ""
    points = 0
    num_comments = 0
    article_url = ""

    try:
        soup = BeautifulSoup(summary, 'html.parser')
        p_tags = soup.find_all('p')
        for p_tag in p_tags:
            if p_tag.text.startswith('Article URL:'):
                article_url = p_tag.text.split(': ')[1]
            if p_tag.text.startswith('Points:'):
                points = p_tag.text.split(': ')[1]
            if p_tag.text.startswith('# Comments:'):
                num_comments = p_tag.text.split(': ')[1]
            else:
                description += p_tag.text
    except Exception as ex:
        logger.error('Error while parsing feed item: %s', ex)

    return FeedItemCreate(
        title=title,
        link=link,
        source_name=source_name,
        local_id=local_id,
        description=summary,
        points=points,
        comments_url=comments,
        article_url=article_url,
        num_comments=num_comments,
        published=published
    )
