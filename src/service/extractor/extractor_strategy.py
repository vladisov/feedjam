from collections.abc import Callable

from service.extractor.generic_extractor import extract_generic
from service.extractor.telegram_extractor import extract_telegram


def get_extractor(source: str) -> Callable[[str], str]:
    if "hackernews" in source:
        return extract_generic
    if "telegram" in source or "tg" in source:
        return extract_telegram
    return extract_generic
