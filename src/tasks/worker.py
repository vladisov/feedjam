from datetime import datetime
import os

from celery import Celery
from celery.schedules import crontab
from sqlmodel import Session
from repository.user_storage import UserStorage
from service.data_extractor import DataExtractor
from service.feed_service import FeedService
from model.schema.feed_schema import RunCreate, SubscriptionUpdate

from repository.db import get_db
from repository.feed_storage import FeedStorage
from repository.run_storage import RunStorage
from repository.subscription_storage import SubscriptionStorage
from src.repository.source_storage import SourceStorage
from utils import config

celery = Celery(__name__)
celery.conf.broker_url = os.environ.get(  # type: ignore
    "CELERY_BROKER_URL", "redis://localhost:6379")
celery.conf.result_backend = os.environ.get(  # type: ignore
    "CELERY_RESULT_BACKEND", "redis://localhost:6379")

celery.conf.beat_schedule = {
    'feed_fetcher': {
        'task': 'schedule_run',
        'schedule': crontab(minute='*/1'),  # execute every minute
    },
    'generate-views': {
        'task': 'generate_views',
        'schedule': crontab(minute='*/1'),  # execute every minute
    },
}

logger = celery.log.get_default_logger()


@celery.task(name="schedule_run")
def schedule_run():
    db: Session = next(get_db())  # type: ignore

    subscription_storage = SubscriptionStorage(db)
    run_storage = RunStorage(db)

    to_run = subscription_storage.get_subscriptions_to_run()

    for subscription in to_run:
        new_run = run_storage.create_run(
            RunCreate(subscription_id=subscription.id, status="pending"))
        do_run.delay(new_run.id)

    return True


@celery.task(name="do_run")
def do_run(run_id: int):
    db = next(get_db())

    feed_storage = FeedStorage(db)
    subscription_storage = SubscriptionStorage(db)
    source_storage = SourceStorage(db)
    data_extractor = DataExtractor(config.OPEN_API_KEY)
    feed_service = FeedService(
        feed_storage, subscription_storage, source_storage, data_extractor)
    run_storage = RunStorage(db)

    try:
        run = run_storage.get_run(run_id)
        if not run:
            raise Exception("Run not found")

        run_storage.update_run_status(run_id, "running")
        feed_service.fetch_and_save_feed_items(run.subscription_id)
        run_storage.update_run_status(run_id, "success")
        subscription_storage.update_subscription(
            SubscriptionUpdate(last_run=datetime.now()), run.subscription_id)
    except Exception as e:
        logger.error(e)
        run_storage.update_run_status(run_id, "failed")
        return False

    return True


@celery.task(name="generate_views")
def generate_views():
    db: Session = next(get_db())  # type: ignore

    # subscription_storage = SubscriptionStorage(db)
    # run_storage = RunStorage(db)
    user_storage = UserStorage(db)

    users_to_run = user_storage.get_active_users()

    for user in users_to_run:
        # new_run = run_storage.create_run(
        #     RunCreate(subscription_id=subscription.id, status="pending"))
        generate_user_view.delay(user.id, 0)

    return True


@celery.task(name="generate_user_view")
def generate_user_view(user_id: int, run_id: int):
    db = next(get_db())

    feed_storage = FeedStorage(db)
    subscription_storage = SubscriptionStorage(db)
    data_extractor = DataExtractor(config.OPEN_API_KEY)
    source_storage = SourceStorage(db)

    feed_service = FeedService(
        feed_storage, subscription_storage, source_storage, data_extractor)
    # run_storage = RunStorage(db)

    try:
        # run = run_storage.get_run(run_id)
        # if not run:
        #     raise Exception("Run not found")

        # run_storage.update_run_status(run_id, "running")
        feed_service.generate_and_save_user_feed(user_id=user_id)
        # run_storage.update_run_status(run_id, "success")
        # subscription_storage.update_subscription(
        #     SubscriptionUpdate(last_run=datetime.now()), run.subscription_id)
    except Exception as e:
        logger.error(e)
        # run_storage.update_run_status(run_id, "failed")
        return False

    return True
