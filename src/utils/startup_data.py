"""Default data for startup initialization."""

from schemas import UserIn

DEFAULT_USERS = [
    UserIn(handle="test1"),
    UserIn(handle="test2"),
]

DEFAULT_SOURCES = [
    ("hackernews", "https://hnrss.org/best"),
    ("telegram_red", "https://t.me/s/redakciya_channel"),
]
