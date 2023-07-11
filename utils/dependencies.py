from fastapi import Depends
from repository.db import get_db
from repository.source_storage import SourceStorage
from repository.subscription_storage import SubscriptionStorage
from repository.user_storage import UserStorage
from service.feed_service import FeedService

from service.subscription.subscription_service import SubscriptionService
from repository.feed_storage import FeedStorage


def get_user_storage(db=Depends(get_db)):
    return UserStorage(db)


def get_subscription_storage(db=Depends(get_db)):
    return SubscriptionStorage(db)


def get_feed_storage(db=Depends(get_db)):
    return FeedStorage(db)


def get_source_storage(db=Depends(get_db)):
    return SourceStorage(db)


def get_feed_service(feed_storage=Depends(get_feed_storage)):
    return FeedService(feed_storage)


def get_subscription_service(feed_storage=Depends(get_feed_storage),
                             subscription_storage=Depends(
                                 get_subscription_storage),
                             source_storage=Depends(get_source_storage)):
    return SubscriptionService(feed_storage, subscription_storage, source_storage)
