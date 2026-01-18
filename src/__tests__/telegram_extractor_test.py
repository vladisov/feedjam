from unittest.mock import MagicMock

from service.extractor import telegram_extractor


def test_extract_telegram_feed(mocker):
    resource_url = "https://t.me/s/redakciya_channel"
    with open("src/__tests__/test_data/page_example.html", encoding="utf-8") as file:
        test_html = file.read()

    mock_requests = mocker.patch("service.extractor.telegram_extractor.requests.get")
    mock_response = MagicMock()
    mock_response.text = test_html
    mock_requests.return_value = mock_response

    data = telegram_extractor.extract_telegram(resource_url)

    mock_requests.assert_called_once_with(resource_url, timeout=3)
    assert data is not None
