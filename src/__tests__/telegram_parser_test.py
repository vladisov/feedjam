from datetime import datetime
from bs4 import BeautifulSoup
from model.schema.feed_schema import SourceSchema

from service.parser import telegram_parser


def test_parse_telegram_feed(mocker):

    source = SourceSchema(id=1, name="telegram",
                          resource_url="https://t.me/s/redakciya_channel",
                          created_at=datetime.now(), is_active=True)
<<<<<<<< HEAD:src/__tests__/telegram_parser_test.py
    with open('src/__tests__/test_data/page_example.html', 'r', encoding='utf-8') as file:
========
    with open('tests/test_data/page_example.html', 'r') as file:
>>>>>>>> main:src/tests/telegram_parser_test.py
        test_html = file.read()

    mock_requests = mocker.patch(
        'service.parser.telegram_parser.requests.get')
    mock_requests.return_value.text = test_html

    mock_bs = mocker.patch(
        'service.parser.telegram_parser.BeautifulSoup')
    mock_bs.return_value = BeautifulSoup(test_html, 'html.parser')

    # Act
    items = telegram_parser.parse_telegram_feed(source)

    # Assert
    mock_requests.assert_called_once_with(source.resource_url)
    mock_bs.assert_called_once_with(
        mock_requests.return_value.text, 'html.parser')

    assert len(items) == 6
