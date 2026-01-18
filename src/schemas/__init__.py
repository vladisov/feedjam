"""Pydantic schemas for API requests and responses.

Naming convention:
- XxxIn: Input schema for creating/updating
- XxxOut: Output schema for responses
- XxxUpdate: Partial update schema
"""

from .feeds import (
    FeedItemIn,
    FeedItemOut,
    ItemState,
    UserFeedItemIn,
    UserFeedItemOut,
    UserFeedOut,
)
from .runs import RunIn, RunOut
from .sources import SourceIn, SourceOut
from .subscriptions import SubscriptionIn, SubscriptionOut, SubscriptionUpdate
from .users import UserIn, UserOut

__all__ = [
    # Users
    "UserIn",
    "UserOut",
    # Sources
    "SourceIn",
    "SourceOut",
    # Subscriptions
    "SubscriptionIn",
    "SubscriptionOut",
    "SubscriptionUpdate",
    # Feeds
    "FeedItemIn",
    "FeedItemOut",
    "UserFeedItemIn",
    "UserFeedItemOut",
    "UserFeedOut",
    "ItemState",
    # Runs
    "RunIn",
    "RunOut",
]
