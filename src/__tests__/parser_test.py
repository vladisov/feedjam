"""Tests for parser registry and source detection."""

from unittest.mock import Mock

from service.parser import detect_source_type, get_parser_for_source, parse_source_name
from service.parser.base import get_parser, get_registered_parsers


def test_registered_parsers_include_all_types():
    """Verify all expected parsers are registered."""
    parsers = get_registered_parsers()
    expected = ["rss", "hackernews", "telegram", "reddit", "youtube", "github"]
    for parser_type in expected:
        assert parser_type in parsers, f"Parser {parser_type} not registered"


def test_get_parser_returns_parser_for_valid_type():
    """Test that get_parser returns a parser for valid types."""
    parser = get_parser("hackernews")
    assert parser is not None


def test_get_parser_returns_none_for_invalid_type():
    """Test that get_parser returns None for unknown types."""
    parser = get_parser("unknown_type")
    assert parser is None


def test_detect_source_type_hackernews():
    """Test HN URL detection."""
    assert detect_source_type("https://hnrss.org/best") == "hackernews"
    assert detect_source_type("https://news.ycombinator.com/rss") == "hackernews"


def test_detect_source_type_reddit():
    """Test Reddit URL detection."""
    assert detect_source_type("https://www.reddit.com/r/programming/.rss") == "reddit"


def test_detect_source_type_youtube():
    """Test YouTube URL detection."""
    assert (
        detect_source_type("https://www.youtube.com/feeds/videos.xml?channel_id=123") == "youtube"
    )


def test_detect_source_type_github():
    """Test GitHub URL detection."""
    assert detect_source_type("https://github.com/anthropics/claude-code/releases.atom") == "github"


def test_detect_source_type_telegram():
    """Test Telegram URL detection."""
    assert detect_source_type("https://t.me/some_channel") == "telegram"


def test_detect_source_type_rss():
    """Test RSS URL detection."""
    assert detect_source_type("https://example.com/feed.rss") == "rss"
    assert detect_source_type("https://example.com/atom.xml") == "rss"


def test_parse_source_name_hackernews():
    """Test HN source name generation."""
    name = parse_source_name("https://hnrss.org/best", "hackernews")
    assert "hackernews" in name


def test_parse_source_name_reddit():
    """Test Reddit source name generation."""
    name = parse_source_name("https://www.reddit.com/r/programming/.rss", "reddit")
    assert "reddit" in name
    assert "programming" in name


def test_parse_source_name_youtube():
    """Test YouTube source name generation."""
    name = parse_source_name(
        "https://www.youtube.com/feeds/videos.xml?channel_id=ABC123", "youtube"
    )
    assert "youtube" in name


def test_parse_source_name_github():
    """Test GitHub source name generation."""
    name = parse_source_name("https://github.com/owner/repo/releases.atom", "github")
    assert "github" in name
    assert "owner" in name
    assert "repo" in name


def test_get_parser_for_source():
    """Test getting parser for a source object."""
    source = Mock()
    source.source_type = "hackernews"
    source.resource_url = "https://hnrss.org/best"

    parser = get_parser_for_source(source)
    assert parser is not None


def test_get_parser_for_source_fallback():
    """Test fallback to RSS parser for unknown source types."""
    source = Mock()
    source.source_type = "unknown"
    source.resource_url = "https://example.com/feed.rss"

    parser = get_parser_for_source(source)
    assert parser is not None  # Should fall back to RSS parser
