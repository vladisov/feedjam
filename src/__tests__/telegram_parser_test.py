"""Tests for TelegramParser."""

from unittest.mock import MagicMock

from service.parser.telegram_parser import TelegramParser


def test_parse_telegram_feed(mocker):
    """Test parsing Telegram channel feed with real HTML fixture."""
    source = MagicMock()
    source.name = "telegram"
    source.resource_url = "https://t.me/s/redakciya_channel"

    with open("src/__tests__/test_data/page_example.html", encoding="utf-8") as file:
        test_html = file.read()

    mock_response = MagicMock()
    mock_response.text = test_html
    mock_response.raise_for_status = MagicMock()
    mocker.patch("service.parser.telegram_parser.requests.get", return_value=mock_response)

    parser = TelegramParser()
    items = parser.parse(source)

    assert len(items) == 7


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
