from unittest.mock import patch, MagicMock
from __tests__.conftest import OPEN_AI_KEY
from service.data_extractor import DataExtractor


def test_parse_web_page_hn():
    data_extractor = DataExtractor(OPEN_AI_KEY)
    filename = "src/__tests__/test_data/mummy-wiki.html"

    with open(filename, 'r', encoding='utf-8') as file:
        hn_file = file.read()

        mock_response = MagicMock()
        mock_response.text = hn_file
        with patch('requests.get', return_value=mock_response):

            text = data_extractor.get_webpage_text("source_name",
                                                   "https://t.me/redakciya_channel/27463")

            assert text is not None  # make a more sophisticated check


def test_parse_web_page_tg():
    data_extractor = DataExtractor(OPEN_AI_KEY)
    filename = "src/__tests__/test_data/telegram-web.html"

    with open(filename, 'r', encoding='utf-8') as file:
        hn_file = file.read()

        mock_response = MagicMock()
        mock_response.text = hn_file

        with patch('requests.get', return_value=mock_response):
            text = data_extractor.get_webpage_text(
                "https://t.me/redakciya_channel/27463")

            assert text is not None
