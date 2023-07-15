from fastapi import Depends, FastAPI, HTTPException
from model.schema.feed_schema import RunSchema, SubscriptionCreate, SubscriptionSchema
from model.schema.user_schema import UserCreate, UserSchema
from repository.run_storage import RunStorage
from repository.user_storage import UserStorage
from service.feed_service import FeedService
from service.subscription.subscription_service import SubscriptionService
from utils.dependencies import get_feed_service, get_run_storage, get_subscription_service
from utils.dependencies import get_user_storage
from repository.db import engine, Base
from utils.logger import get_logger

# logging.config.fileConfig(
#     'logging.conf', disable_existing_loggers=False)

# logger = logging.getLogger(__name__)

# Base.metadata.drop_all(bind=engine)  # type: ignore
Base.metadata.create_all(bind=engine)  # type: ignore

app = FastAPI()
logger = get_logger(__name__)


@app.on_event("startup")
def on_startup():
    pass


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


@app.get("/feed/{user_id}")
async def get_feed(user_id: int,
                   feed_service: FeedService = Depends(get_feed_service)) -> dict:
    user_feed = feed_service.get_user_feed(user_id)
    if not user_feed:
        raise HTTPException(status_code=404, detail="Feed not found")
    return {"data": user_feed}


@app.post("/subscribe")
async def subscribe(subscription: SubscriptionCreate,
                    subscription_service: SubscriptionService =
                    Depends(get_subscription_service)) -> dict:

    subscription_schema = subscription_service.add_subscription(subscription)
    return {"message": "Subscribed successfully!", "data": subscription_schema}


@app.get("/subscriptions", response_model=list[SubscriptionSchema],)
def get_subscriptions(user_id: int, sub_service: SubscriptionService = Depends(get_subscription_service)):
    subscriptions = sub_service.get_user_subscriptions(user_id)
    return subscriptions


@app.get("/runs", response_model=list[RunSchema],)
def get_runs(subscription_id: int, run_storage: RunStorage = Depends(get_run_storage)):
    subscriptions = run_storage.get_runs_by_subscription(subscription_id)
    return subscriptions


# extractor = DataExtractor(
#     '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')


# @app.post("/feed/add")
# async def add_post(post: Post):
#     summary = extractor.extract_and_summarize(post.post_url)
#     post_data = {**post.dict(), "summary": summary, "link": post.post_url}
#     posts.append(post_data)
#     return {"message": "Feed added successfully!", "data": post_data}
