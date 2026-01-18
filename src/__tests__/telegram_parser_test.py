"""Tests for TelegramParser."""

from unittest.mock import MagicMock

from bs4 import BeautifulSoup

from service.parser.telegram_parser import TelegramParser


def test_parse_telegram_feed(mocker):
    """Test parsing Telegram channel feed."""
    source = MagicMock()
    source.name = "telegram"
    source.resource_url = "https://t.me/s/redakciya_channel"

    with open("src/__tests__/test_data/page_example.html", encoding="utf-8") as file:
        test_html = file.read()

    mock_requests = mocker.patch("service.parser.telegram_parser.requests.get")
    mock_requests.return_value.text = test_html

    mock_bs = mocker.patch("service.parser.telegram_parser.BeautifulSoup")
    mock_bs.return_value = BeautifulSoup(test_html, "html.parser")

    # Use the new class-based parser
    parser = TelegramParser()
    items = parser.parse(source)

    # Assert
    mock_requests.assert_called_once_with(source.resource_url, timeout=30)
    mock_bs.assert_called_once_with(mock_requests.return_value.text, "html.parser")

    assert len(items) == 6


def test_can_handle_telegram_urls():
    """Test TelegramParser.can_handle for various URLs."""
    assert TelegramParser.can_handle("https://t.me/some_channel") is True
    assert TelegramParser.can_handle("https://t.me/s/some_channel") is True
    assert TelegramParser.can_handle("https://telegram.me/channel") is True
    assert TelegramParser.can_handle("https://example.com/feed") is False


def test_get_source_name():
    """Test generating source name from Telegram URL."""
    parser = TelegramParser()
    assert parser.get_source_name("https://t.me/s/python_channel") == "telegram-python_channel"
    assert parser.get_source_name("https://t.me/tech_news/") == "telegram-tech_news"
