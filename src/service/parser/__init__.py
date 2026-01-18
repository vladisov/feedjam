"""Feed parser module.

This module provides extensible feed parsing with a registry pattern.

To add a new parser:
1. Create a new file in service/parser/ (e.g., reddit_parser.py)
2. Implement a class that inherits from BaseParser
3. Register it with the @register_parser decorator
4. Add the source type to model/source.py SourceType enum

Example:
    # In service/parser/reddit_parser.py
    from service.parser.base import BaseParser, register_parser

    @register_parser("reddit")
    class RedditParser(BaseParser):
        @classmethod
        def can_handle(cls, url: str) -> bool:
            return "reddit.com" in url

        def parse(self, source: Source) -> list[FeedItemIn]:
            # Your implementation here
            ...

The parser will be automatically registered and available.
"""

from service.parser.base import BaseParser, get_registered_parsers, register_parser
from service.parser.source_parser_strategy import (
    detect_source_type,
    get_parser_for_source,
    parse_source,
    parse_source_name,
)

__all__ = [
    "BaseParser",
    "register_parser",
    "get_parser_for_source",
    "detect_source_type",
    "get_registered_parsers",
    "parse_source_name",
    "parse_source",
]
