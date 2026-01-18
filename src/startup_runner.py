"""Startup initialization - creates default data."""

from datetime import datetime

from repository.db import get_db_session
from repository.feed_storage import FeedStorage
from repository.run_storage import RunStorage
from repository.source_storage import SourceStorage
from repository.subscription_storage import SubscriptionStorage
from repository.user_storage import UserStorage
from schemas import RunIn, SourceIn, SubscriptionUpdate, UserIn
from service.data_extractor import DataExtractor
from service.feed_service import FeedService
from utils import config
from utils.logger import get_logger
from utils.startup_data import DEFAULT_SOURCES, DEFAULT_USERS

logger = get_logger(__name__)


def on_startup(app):
    """Initialize default data on startup."""
    with get_db_session() as db:
        _run_startup(db)


def _run_startup(db):
    """Create default users, sources, and subscriptions."""
    user_storage = UserStorage(db)
    source_storage = SourceStorage(db)
    subscription_storage = SubscriptionStorage(db)
    run_storage = RunStorage(db)
    feed_storage = FeedStorage(db)
    data_extractor = DataExtractor(config.OPEN_AI_KEY)
    feed_service = FeedService(feed_storage, subscription_storage, source_storage, data_extractor)

    # 1. Create default users
    users = []
    for user_data in DEFAULT_USERS:
        if not user_storage.get_by_handle(user_data.handle):
            users.append(user_storage.create(UserIn(handle=user_data.handle)))
    logger.info(f"Created {len(users)} users")

    # 2. Create default sources
    sources = [
        source_storage.create(SourceIn(name=name, resource_url=url))
        for name, url in DEFAULT_SOURCES
    ]
    logger.info(f"Created/found {len(sources)} sources")

    # 3. Create subscriptions
    subscriptions = []
    for user, source in zip(users, sources, strict=False):
        sub = subscription_storage.create(user.id, source.id)
        subscriptions.append(sub)
    logger.info(f"Created {len(subscriptions)} subscriptions")

    # 4. Schedule initial runs
    run_storage.create(RunIn(job_type="all_subscriptions", status="pending"))
    run_storage.create(RunIn(job_type="all_user_views", status="pending"))

    # 5. Fetch and generate feeds immediately
    for sub in subscription_storage.get_due_for_run():
        feed_service.fetch_and_save_items(sub.id)
        subscription_storage.update(
            sub.id, SubscriptionUpdate(is_active=True, last_run=datetime.now())
        )

    for user in user_storage.get_active():
        feed_service.generate_user_feed(user.id)
