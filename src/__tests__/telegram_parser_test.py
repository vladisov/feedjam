from unittest.mock import MagicMock

from bs4 import BeautifulSoup

from service.parser import telegram_parser


def test_parse_telegram_feed(mocker):
    source = MagicMock()
    source.name = "telegram"
    source.resource_url = "https://t.me/s/redakciya_channel"
    with open("src/__tests__/test_data/page_example.html", encoding="utf-8") as file:
        test_html = file.read()

    mock_requests = mocker.patch("service.parser.telegram_parser.requests.get")
    mock_requests.return_value.text = test_html

    mock_bs = mocker.patch("service.parser.telegram_parser.BeautifulSoup")
    mock_bs.return_value = BeautifulSoup(test_html, "html.parser")

    # Act
    items = telegram_parser.parse_telegram_feed(source)

    # Assert
    mock_requests.assert_called_once_with(source.resource_url)
    mock_bs.assert_called_once_with(mock_requests.return_value.text, "html.parser")

    assert len(items) == 6
