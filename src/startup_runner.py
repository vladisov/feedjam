from datetime import datetime
from model.schema.feed_schema import RunCreate, SourceCreate, SubscriptionCreate, SubscriptionUpdate
from repository.db import get_db
from repository.feed_storage import FeedStorage
from repository.run_storage import RunStorage
from repository.user_storage import UserStorage
from service.data_extractor import DataExtractor
from service.feed_service import FeedService
from utils import config
from utils.logger import get_logger
from utils.startup_data import DEFAULT_SOURCES, DEFAULT_USERS
from repository.source_storage import SourceStorage
from repository.subscription_storage import SubscriptionStorage

logger = get_logger(__name__)


def on_startup(app):
    db = next(get_db())  # type: ignore
    user_storage, source_storage, sub_storage, run_storage, feed_storage = (
        UserStorage(db),
        SourceStorage(db),
        SubscriptionStorage(db),
        RunStorage(db),
        FeedStorage(db)
    )
    data_extractor = DataExtractor(config.OPEN_AI_KEY)
    feed_service = FeedService(
        feed_storage, sub_storage, source_storage, data_extractor)

    # 1. Create default users, sources and subscriptions
    users = [user_storage.create_user(user=user_data)
             for user_data in DEFAULT_USERS
             if not user_storage.get_user_by_handle(handle=user_data.handle)]
    logger.info(f"Created {len(users)} users")

    sources = [source_storage.create_source(
        SourceCreate(name=source_name, resource_url=url))
        for source_name, url in DEFAULT_SOURCES]
    logger.info(f"Created {len(sources)} sources")

    subscriptions = [sub_storage.create_subscription(
        SubscriptionCreate(user_id=user.id, source_id=source.id, resource_url=source.resource_url))
        for user, source in zip(users, sources)]
    logger.info(f"Created {len(subscriptions)} subscriptions")

    # 2. Schedule runs for worker (mostly to make sure it's working correctly)
    run_storage.create_run(
        RunCreate(job_type="all_subscriptions", status="pending"))
    run_storage.create_run(
        RunCreate(job_type="all_user_views", status="pending"))

    # 3. Fetch and save feed items for all subscriptions
    for subscription in sub_storage.get_subscriptions_to_run():
        feed_service.fetch_and_save_feed_items(subscription.id)
        sub_storage.update_subscription(
            SubscriptionUpdate(id=subscription.id, is_active=True, last_run=datetime.now()), subscription.id)
    for user in user_storage.get_active_users():
        feed_service.generate_and_save_user_feed(user_id=user.id)
