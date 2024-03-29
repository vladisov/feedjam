from fastapi import Depends, FastAPI, HTTPException
from model.schema.feed_schema import RunCreate, RunSchema, SubscriptionCreateAPI, SubscriptionSchema
from model.schema.feed_schema import UserCreate, UserFeedSchema, UserSchema
from repository.db import engine, Base
from repository.run_storage import RunStorage
from repository.user_storage import UserStorage
from service.feed_service import FeedService
from service.subscription_service import SubscriptionService
from utils.config import CREATE_ITEMS_ON_STARTUP
from utils.dependencies import get_feed_service, get_run_storage, get_subscription_service
from utils.dependencies import get_user_storage
from utils.logger import get_logger
from startup_runner import on_startup  # noqa
import ssl

ssl._create_default_https_context = ssl._create_unverified_context  # I don't know WHY

# Base.metadata.drop_all(bind=engine)  # type: ignore
Base.metadata.create_all(bind=engine)  # type: ignore

app = FastAPI()
logger = get_logger(__name__)


@app.on_event("startup")
def startup_event():
    if CREATE_ITEMS_ON_STARTUP:
        on_startup(app)


@app.post("/users/", response_model=UserSchema)
def create_user(user: UserCreate,
                user_storage: UserStorage = Depends(get_user_storage)):
    db_user = user_storage.get_user_by_handle(handle=user.handle)
    if db_user:
        raise HTTPException(
            status_code=400, detail="Handle already registered")
    return user_storage.create_user(user=user)


@app.get("/users/", response_model=list[UserSchema],)
def get_users(skip: int = 0, limit: int = 100,
              user_storage: UserStorage = Depends(get_user_storage)):
    users = user_storage.get_users(skip=skip, limit=limit)
    return users


@app.get("/feed/{user_id}", response_model=UserFeedSchema)
async def get_feed(user_id: int,
                   feed_service: FeedService = Depends(get_feed_service)) -> UserFeedSchema:
    user_feed = feed_service.get_user_feed(user_id)
    if not user_feed:
        raise HTTPException(status_code=404, detail="Feed not found")
    return user_feed


@app.post("/subscribe")
async def subscribe(subscription: SubscriptionCreateAPI,
                    subscription_service: SubscriptionService =
                    Depends(get_subscription_service)) -> SubscriptionSchema:

    subscription_schema = subscription_service.add_subscription(subscription)
    return subscription_schema


@app.get("/subscriptions", response_model=list[SubscriptionSchema],)
def get_subscriptions(user_id: int, sub_service: SubscriptionService = Depends(get_subscription_service)):
    subscriptions = sub_service.get_user_subscriptions(user_id)
    return subscriptions


@app.get("/runs", response_model=list[RunSchema],)
def get_runs(run_storage: RunStorage = Depends(get_run_storage)):
    runs = run_storage.get_all_runs()
    return runs


@app.get("/runs/{id}", response_model=list[RunSchema],)
def get_runs_by_id(subscription_id: int, run_storage: RunStorage = Depends(get_run_storage)):
    runs = run_storage.get_runs_by_subscription(subscription_id)
    return runs


@app.post("/runs/", response_model=RunSchema)
def create_run(run: RunCreate,
               run_storage: RunStorage = Depends(get_run_storage)):
    return run_storage.create_run(run=run)


@app.get("/user/{user_id}", response_model=UserSchema)
def get_account_details(user_id: int, user_storage: UserStorage = Depends(get_user_storage)):
    logger.info(f"Fetching user {user_id}")
    user = user_storage.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
