"""Background scheduler using APScheduler.

Handles periodic tasks like fetching subscriptions and generating feeds.
"""

from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from repository.db import get_db_session
from repository.subscription_storage import SubscriptionStorage
from repository.user_storage import UserStorage
from schemas import SubscriptionUpdate
from service.factory import ServiceFactory
from utils.logger import get_logger

logger = get_logger(__name__)


def _create_factory_with_user_key(db, user_id: int) -> ServiceFactory:
    """Create a ServiceFactory configured with the user's API key."""
    user_api_key = UserStorage(db).get_openai_key(user_id)
    return ServiceFactory(db, openai_key=user_api_key)

scheduler = BackgroundScheduler()


def fetch_subscription(subscription_id: int) -> bool:
    """Fetch and save feed items for a single subscription."""
    with get_db_session() as db:
        subscription = SubscriptionStorage(db).get(subscription_id)
        if not subscription:
            logger.error(f"Subscription {subscription_id} not found")
            return False

        factory = _create_factory_with_user_key(db, subscription.user_id)

        try:
            factory.feed_service.fetch_and_save_items(subscription_id)
            factory.subscription_storage.update(
                subscription_id,
                SubscriptionUpdate(is_active=True, last_run=datetime.now()),
            )
            logger.info(f"Successfully fetched subscription {subscription_id}")
            return True

        except Exception as e:
            logger.error(f"Error fetching subscription {subscription_id}: {e}")
            return False


def generate_user_feed(user_id: int) -> bool:
    """Generate personalized feed for a user."""
    with get_db_session() as db:
        factory = _create_factory_with_user_key(db, user_id)

        try:
            factory.feed_service.generate_user_feed(user_id)
            logger.info(f"Generated feed for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error generating feed for user {user_id}: {e}")
            return False


def scheduled_fetch_all() -> None:
    """Scheduled job: fetch all active subscriptions."""
    logger.info("Running scheduled fetch for all subscriptions")
    with get_db_session() as db:
        factory = ServiceFactory(db)
        subscriptions = factory.subscription_storage.get_due_for_run()

        for sub in subscriptions:
            fetch_subscription(sub.id)


def scheduled_generate_feeds() -> None:
    """Scheduled job: generate feeds for all active users."""
    logger.info("Running scheduled feed generation for all users")
    with get_db_session() as db:
        factory = ServiceFactory(db)
        users = factory.user_storage.get_active()

        for user in users:
            generate_user_feed(user.id)


def process_pending_runs() -> None:
    """Process any manually created pending runs."""
    with get_db_session() as db:
        factory = ServiceFactory(db)
        pending_runs = factory.run_storage.get_pending()

        for run in pending_runs:
            factory.run_storage.update_status(run.id, "running")

            try:
                success = False
                if run.job_type == "single_subscription" and run.subscription_id:
                    success = fetch_subscription(run.subscription_id)
                elif run.job_type == "single_user_view" and run.user_id:
                    success = generate_user_feed(run.user_id)
                elif run.job_type == "all_subscriptions":
                    scheduled_fetch_all()
                    success = True
                elif run.job_type == "all_user_views":
                    scheduled_generate_feeds()
                    success = True
                else:
                    logger.warning(f"Unknown job type: {run.job_type}")

                factory.run_storage.update_status(run.id, "success" if success else "failed")

            except Exception as e:
                logger.error(f"Error processing run {run.id}: {e}")
                factory.run_storage.update_status(run.id, "failed")


def start_scheduler() -> None:
    """Start the background scheduler with configured jobs."""
    # Process pending runs every minute
    scheduler.add_job(
        process_pending_runs,
        trigger=IntervalTrigger(minutes=1),
        id="process_pending_runs",
        replace_existing=True,
    )

    # Fetch subscriptions every 30 minutes
    scheduler.add_job(
        scheduled_fetch_all,
        trigger=IntervalTrigger(minutes=30),
        id="fetch_all_subscriptions",
        replace_existing=True,
    )

    # Generate user feeds every 30 minutes
    scheduler.add_job(
        scheduled_generate_feeds,
        trigger=IntervalTrigger(minutes=30),
        id="generate_all_feeds",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("Background scheduler started")


def stop_scheduler() -> None:
    """Stop the background scheduler."""
    scheduler.shutdown(wait=False)
    logger.info("Background scheduler stopped")
