import os

from celery import Celery
from celery.schedules import crontab
from sqlmodel import Session
from model.schema.feed_schema import RunCreate, SubscriptionUpdate
from service.data_extractor import DataExtractor
from service.feed_service import FeedService
from repository.user_storage import UserStorage
from repository.db import get_db
from repository.feed_storage import FeedStorage
from repository.run_storage import RunStorage
from repository.subscription_storage import SubscriptionStorage
from repository.source_storage import SourceStorage
from utils import config

celery = Celery(__name__)
celery.conf.broker_url = os.environ.get(  # type: ignore
    "CELERY_BROKER_URL", "redis://localhost:6379")
celery.conf.result_backend = os.environ.get(  # type: ignore
    "CELERY_RESULT_BACKEND", "redis://localhost:6379")
FETCHER_INTERVAL = os.environ.get('FETCHER_INTERVAL', '*/5')


celery.conf.beat_schedule = {
    'feed_fetcher': {
        'task': 'schedule_run',
        'schedule': crontab(minute=FETCHER_INTERVAL),
    },
    'generate-views': {
        'task': 'generate_views',
        'schedule': crontab(minute=FETCHER_INTERVAL),
    },
}

logger = celery.log.get_default_logger()


@celery.task(name="generic_job_runner")
def job_runner() -> bool:
    db: Session = next(get_db())  # type: ignore
    run_storage = RunStorage(db)
    run_storage.get_all_pending_runs()

    for run in run_storage.get_all_pending_runs():
        if run.job_type == 'all_subscriptions':
            schedule_each_sub.delay(run.id)
        elif run.job_type == 'single_subscription':
            sub_run.delay(run.id, run.subscription_id)
        elif run.job_type == 'all_user_views':
            generate_all_views.delay(run.id)
        elif run.job_type == 'single_user_view':
            generate_single_user_view.delay(run.id, run.user_id)
    return True


@celery.task(name="schedule_all_subs")
def schedule_all_subs() -> bool:
    db: Session = next(get_db())  # type: ignore
    run_storage = RunStorage(db)
    # potentially get count of subs first
    new_run = run_storage.create_run(
        RunCreate(job_type='all_subscriptions', status="pending"))
    return new_run is not None


@celery.task(name="schedule_all_views_generation")
def schedule_all_views_generation() -> bool:
    db: Session = next(get_db())  # type: ignore
    run_storage = RunStorage(db)
    # potentially get count of subs first
    new_run = run_storage.create_run(
        RunCreate(job_type='all_user_views', status="pending"))
    return new_run is not None


@celery.task(name="schedule_each_sub")
def schedule_each_sub(run_id: int) -> bool:
    db: Session = next(get_db())  # type: ignore

    run_storage = RunStorage(db)
    sub_storage = SubscriptionStorage(db)
    run_storage.update_run_status(run_id, "running")

    for sub in sub_storage.get_subscriptions():
        run_storage.create_run(
            RunCreate(job_type='single_subscription', status="pending", subscription_id=sub.id))
        # sub_run.delay(new_run.id)

    run_storage.update_run_status(run_id, "success")
    # add failed logic
    return True


@celery.task(name="do_run")
def sub_run(run_id: int, subscription_id: int) -> bool:
    db = next(get_db())

    feed_storage = FeedStorage(db)
    subscription_storage = SubscriptionStorage(db)
    source_storage = SourceStorage(db)
    data_extractor = DataExtractor(config.OPEN_AI_KEY)
    feed_service = FeedService(
        feed_storage, subscription_storage, source_storage, data_extractor)
    run_storage = RunStorage(db)

    try:
        run = run_storage.get_run(run_id)
        if not run:
            raise Exception("Run not found")

        run_storage.update_run_status(run_id, "running")
        feed_service.fetch_and_save_feed_items(subscription_id)
        run_storage.update_run_status(run_id, "success")
        subscription_storage.update_subscription(
            SubscriptionUpdate(), subscription_id)
    except Exception as ex:
        logger.error("Error while running task: %s", ex)
        run_storage.update_run_status(run_id, "failed")
        return False

    return True


@celery.task(name="generate_all_views")
def generate_all_views(run_id: int) -> bool:
    db: Session = next(get_db())  # type: ignore

    # subscription_storage = SubscriptionStorage(db)
    run_storage = RunStorage(db)
    user_storage = UserStorage(db)

    users_to_run = user_storage.get_active_users()
    run_storage.update_run_status(run_id, "running")
    for user in users_to_run:
        run_storage.create_run(
            RunCreate(status="pending", job_type="single_user_view", user_id=user.id))

        # generate_user_view.delay(user.id) not required

    run_storage.update_run_status(run_id, "success")
    return True


@celery.task(name="generate_single_user_view")
def generate_single_user_view(run_id: int, user_id: int):
    db = next(get_db())

    feed_storage = FeedStorage(db)
    subscription_storage = SubscriptionStorage(db)
    data_extractor = DataExtractor(config.OPEN_AI_KEY)
    source_storage = SourceStorage(db)

    feed_service = FeedService(
        feed_storage, subscription_storage, source_storage, data_extractor)
    run_storage = RunStorage(db)

    try:
        run = run_storage.get_run(run_id)
        if not run:
            raise Exception("Run not found")

        run_storage.update_run_status(run_id, "running")
        feed_service.generate_and_save_user_feed(user_id=user_id)
        run_storage.update_run_status(run_id, "success")
        # subscription_storage.update_subscription(
        #     SubscriptionUpdate(last_run=datetime.now()), run.subscription_id)
    except Exception as ex:
        logger.error(ex)
        run_storage.update_run_status(run_id, "failed")
        return False

    return True
