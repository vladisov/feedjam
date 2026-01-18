from unittest.mock import Mock

import pytest

from service.parser.hn_parser import parse_hn_feed
from service.parser.source_parser_strategy import get_parser, parse_name


@pytest.fixture
def source_mock():
    return Mock()


def test_get_parser_returns_hackernews_parser(source_mock):
    source_mock.name = "hackernews"
    result = get_parser(source_mock)
    assert result == parse_hn_feed


def test_get_parser_returns_none(source_mock):
    source_mock.name = "lol"
    source_mock.resource_url = "lol"
    result = get_parser(source_mock)
    assert result is None


def test_parse_name_hackernews():
    url = "http://www.hackernews.com"
    assert "hackernews" in parse_name(url)


def test_parse_name_hn():
    url = "https://hnrss.org/best"
    assert "hackernews" in parse_name(url)


def test_parse_name_non_hackernews():
    url = "http://www.somewebsite.com"
    assert url in parse_name(url)
