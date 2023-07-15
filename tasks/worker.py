from datetime import datetime
import os

from celery import Celery
from celery.schedules import crontab
from sqlmodel import Session
from service.feed_service import FeedService
from model.schema.feed_schema import RunCreate, SubscriptionUpdate

from repository.db import get_db
from repository.feed_storage import FeedStorage
from repository.run_storage import RunStorage
from repository.subscription_storage import SubscriptionStorage

celery = Celery(__name__)
celery.conf.broker_url = os.environ.get(  # type: ignore
    "CELERY_BROKER_URL", "redis://localhost:6379")
celery.conf.result_backend = os.environ.get(  # type: ignore
    "CELERY_RESULT_BACKEND", "redis://localhost:6379")

celery.conf.beat_schedule = {
    'run-scheduler': {
        'task': 'schedule_run',
        'schedule': crontab(minute='*/10'),  # execute every 10 minutes
        # 'schedule': 10.0,
    },
}


@celery.task(name="schedule_run")
def schedule_run():
    print('Task done!')

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
    feed_service = FeedService(feed_storage, subscription_storage)
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
        print(e)
        run_storage.update_run_status(run_id, "failed")

    return True
