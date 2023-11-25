from typing import List
from bs4 import BeautifulSoup
from dateutil import parser
import requests
import html2text


from model.schema.feed_schema import FeedItemCreate, SourceSchema
from utils.logger import get_logger
from utils.utils import parse_format

logger = get_logger(__name__)


def parse_telegram_feed(source: SourceSchema) -> List[FeedItemCreate]:
    items = parse_telegram_items(source.resource_url)
    feed_items = []
    for item in items:
        try:
            feed_item = _create_telegram_feed_item(item, source)
            feed_items.append(feed_item)
        except Exception as ex:
            logger.error(f'Error while parsing feed item: {ex}')
    return feed_items


def _create_telegram_feed_item(item, source: SourceSchema) -> FeedItemCreate:
    title = item.get('message', '')
    link = item.get('post_link', '')
    views_str = item.get('views', 0)
    views = parse_format(views_str)
    published = item.get('datetime', '')
    if published:
        published = parser.parse(published)

    return FeedItemCreate(
        title=title,
        link=link,
        description=title,
        views=views,
        comments_url=None,
        article_url=link,
        num_comments=0,
        local_id=link,
        published=published
    )


def parse_telegram_items(url) -> list:
    res = requests.get(url)
    soup = BeautifulSoup(res.text, 'html.parser')
    messages = soup.find_all(
        'div', class_='tgme_widget_message text_not_supported_wrap js-widget_message')

    feed_items = []

    for message in messages:
        feed_item = {}

        # Extract main message
        text_div = message.find('div', class_='tgme_widget_message_text')
        if text_div is not None:
            feed_item['message'] = html2text.html2text(text_div.text)

        # Extract metadata
        meta_div = message.find(
            'div', class_='tgme_widget_message_info short js-message_info')
        if meta_div is not None:
            views = meta_div.find('span', class_='tgme_widget_message_views')
            if views is not None:
                feed_item['views'] = views.text

            date_time = meta_div.find('time', class_='time')
            if date_time is not None:
                feed_item['datetime'] = date_time['datetime']

            post_link = meta_div.find('a', class_='tgme_widget_message_date')
            if post_link is not None:
                feed_item['post_link'] = post_link['href']

        feed_items.append(feed_item)

    return feed_items
