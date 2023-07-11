import os

from celery import Celery
from celery.schedules import crontab
from sqlmodel import Session
from service.feed_service import FeedService
from model.schema.feed_schema import RunCreate

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
        'schedule': crontab(minute='*/1'),  # execute every 10 minutes
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
        # insert pending run
        new_run = run_storage.create_run(
            RunCreate(subscription_id=subscription.id, status="pending"))
        do_run.delay(new_run.id)
    # 1. Get all subscriptions
    # 2. For each subscription, check if it's time to run (if it's active and latest run was more than 1 hour ago)
    # 3. If it's time to run, run it in separate task

    return True


@celery.task(name="do_run")
def do_run(run_id: int):
    db = next(get_db())

    feed_storage = FeedStorage(db)
    feed_service = FeedService(feed_storage)
    run_storage = RunStorage(db)

    try:
        run_storage.update_run_status(run_id, "running")
        feed_service.fetch_feed(run_id)
    except Exception as e:
        print(e)
        run_storage.update_run_status(run_id, "failed")
    # subscription_service = SubscriptionService(db)

    # # Assuming run_subscription fetches data from source and saves to db
    # subscription_service.run_subscription(subscription_id)

    # # Updating last_run time
    # subscription = db.query(Subscription).filter(Subscription.id == subscription_id).first()
    # subscription.last_run = datetime.now()
    # db.commit()
    # 1. run subscription
    # 2. fetch data from source
    # 3. save data to db

    return True
