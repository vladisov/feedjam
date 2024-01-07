from model.schema.feed_schema import UserCreate


DEFAULT_USERS = [
    UserCreate(handle="test1"),
    UserCreate(handle="test2")
]

DEFAULT_SOURCES = [
    ("hackernews", "https://hnrss.org/best"),
    ("telegram_red", "https://t.me/s/redakciya_channel")
]
