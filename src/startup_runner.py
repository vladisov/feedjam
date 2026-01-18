"""Startup initialization - creates default data."""

from datetime import datetime

from repository.db import get_db
from schemas import RunIn, SourceIn, SubscriptionUpdate, UserIn
from service.factory import ServiceFactory
from utils.logger import get_logger
from utils.startup_data import DEFAULT_SOURCES, DEFAULT_USERS

logger = get_logger(__name__)


def on_startup(app):
    """Initialize default data on startup."""
    with get_db() as db:
        _run_startup(db)


def _run_startup(db):
    """Create default users, sources, and subscriptions."""
    factory = ServiceFactory(db)

    # 1. Create default users
    users = []
    for user_data in DEFAULT_USERS:
        if not factory.user_storage.get_by_handle(user_data.handle):
            users.append(factory.user_storage.create(UserIn(handle=user_data.handle)))
    logger.info(f"Created {len(users)} users")

    # 2. Create default sources
    sources = [
        factory.source_storage.create(SourceIn(name=name, resource_url=url))
        for name, url in DEFAULT_SOURCES
    ]
    logger.info(f"Created/found {len(sources)} sources")

    # 3. Create subscriptions
    subscriptions = []
    for user, source in zip(users, sources, strict=False):
        sub = factory.subscription_storage.create(user.id, source.id)
        subscriptions.append(sub)
    logger.info(f"Created {len(subscriptions)} subscriptions")

    # 4. Schedule initial runs
    factory.run_storage.create(RunIn(job_type="all_subscriptions", status="pending"))
    factory.run_storage.create(RunIn(job_type="all_user_views", status="pending"))

    # 5. Fetch and generate feeds immediately
    for sub in factory.subscription_storage.get_due_for_run():
        factory.feed_service.fetch_and_save_items(sub.id)
        factory.subscription_storage.update(
            sub.id, SubscriptionUpdate(is_active=True, last_run=datetime.now())
        )

    for user in factory.user_storage.get_active():
        factory.feed_service.generate_user_feed(user.id)
