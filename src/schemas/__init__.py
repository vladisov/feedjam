"""Pydantic schemas for API requests and responses.

Naming convention:
- XxxIn: Input schema for creating/updating
- XxxOut: Output schema for responses
- XxxUpdate: Partial update schema
"""

from .auth import AuthUserOut, RefreshTokenIn, TokenOut, UserLoginIn, UserRegisterIn
from .feeds import (
    FeedItemIn,
    FeedItemOut,
    ItemState,
    UserFeedItemIn,
    UserFeedItemOut,
    UserFeedOut,
)
from .interests import UserInterestIn, UserInterestOut, UserInterestsBulkIn
from .runs import RunIn, RunOut
from .sources import SourceIn, SourceOut
from .subscriptions import SubscriptionIn, SubscriptionOut, SubscriptionUpdate
from .users import UserIn, UserOut, UserSettingsIn, UserSettingsOut

__all__ = [
    # Auth
    "UserRegisterIn",
    "UserLoginIn",
    "TokenOut",
    "RefreshTokenIn",
    "AuthUserOut",
    # Users
    "UserIn",
    "UserOut",
    "UserSettingsIn",
    "UserSettingsOut",
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
    # Interests
    "UserInterestIn",
    "UserInterestOut",
    "UserInterestsBulkIn",
    # Runs
    "RunIn",
    "RunOut",
]
