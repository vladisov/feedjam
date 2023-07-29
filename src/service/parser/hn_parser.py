from datetime import datetime
from typing import List
from bs4 import BeautifulSoup
import feedparser
from model.schema.feed_schema import FeedItemCreate, SourceSchema


def parse_hn_feed(source: SourceSchema) -> List[FeedItemCreate]:
    feed = feedparser.parse(source.resource_url)
    items = list(map(lambda item: _crete_hn_feed_item(
        item, source), feed.entries))
    return items


def _crete_hn_feed_item(item, source: SourceSchema) -> FeedItemCreate:
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
        for p in p_tags:
            if p.text.startswith('Article URL:'):
                article_url = p.text.split(': ')[1]
            if p.text.startswith('Points:'):
                points = p.text.split(': ')[1]
            if p.text.startswith('# Comments:'):
                num_comments = p.text.split(': ')[1]
            else:
                description += p.text
    except Exception as e:
        print(e)

    return FeedItemCreate(
        title=title,
        link=link,
        local_id=local_id,
        description=summary,
        points=points,
        comments_url=comments,
        article_url=article_url,
        num_comments=num_comments,
        published=published
    )
