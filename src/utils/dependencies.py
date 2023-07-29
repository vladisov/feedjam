from fastapi import Depends
from service.data_extractor import DataExtractor
from repository.db import get_db
from repository.run_storage import RunStorage
from repository.source_storage import SourceStorage
from repository.subscription_storage import SubscriptionStorage
from repository.user_storage import UserStorage
from service.feed_service import FeedService

from service.subscription_service import SubscriptionService
from repository.feed_storage import FeedStorage
from utils import config


def get_user_storage(db=Depends(get_db)):
    return UserStorage(db)


def get_subscription_storage(db=Depends(get_db)):
    return SubscriptionStorage(db)


def get_feed_storage(db=Depends(get_db)):
    return FeedStorage(db)


def get_source_storage(db=Depends(get_db)):
    return SourceStorage(db)


def get_run_storage(db=Depends(get_db)):
    return RunStorage(db)


def get_data_extractor():
    return DataExtractor(config.OPEN_API_KEY)


def get_feed_service(feed_storage=Depends(get_feed_storage), subscription_storage=Depends(get_subscription_storage),
                     source_storage=Depends(get_source_storage),
                     data_extractor=Depends(get_data_extractor)):
    return FeedService(feed_storage, subscription_storage, source_storage, data_extractor)


def get_subscription_service(feed_storage=Depends(get_feed_storage),
                             subscription_storage=Depends(
                                 get_subscription_storage),
                             source_storage=Depends(get_source_storage)):
    return SubscriptionService(feed_storage, subscription_storage, source_storage)
