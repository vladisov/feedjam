from datetime import datetime
from bs4 import BeautifulSoup
from model.schema.feed_schema import SourceSchema

from service.extractor import telegram_extractor


def test_extract_telegram_feed(mocker):

    source = SourceSchema(id=1, name="telegram",
                          resource_url="https://t.me/s/redakciya_channel",
                          created_at=datetime.now(), is_active=True)
    with open('src/__tests__/test_data/page_example.html', 'r', encoding='utf-8') as file:
        test_html = file.read()

    mock_requests = mocker.patch(
        'service.parser.telegram_parser.requests.get')
    mock_requests.return_value.text = test_html

    mock_bs = mocker.patch(
        'service.parser.telegram_parser.BeautifulSoup')
    mock_bs.return_value = BeautifulSoup(test_html, 'html.parser')

    # Actfrom model.schema.user_schema
    data = telegram_extractor.extract_telegram(source.resource_url)

    # Assert
    # mock_requests.assert_called_once_with(source.resource_url)
    # mock_bs.assert_called_once_with(
    #     mock_requests.return_value.text, 'html.parser')
