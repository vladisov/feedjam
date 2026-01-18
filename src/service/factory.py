"""Service factory for background tasks.

Use this ONLY for background tasks (scheduler, startup_runner, CLI scripts)
that don't have access to FastAPI's request-scoped dependency injection.

For FastAPI endpoints, use the dependencies in utils/dependencies.py instead,
which uses FastAPI's native DI system.

Usage:
    with get_db_session() as db:
        factory = ServiceFactory(db)
        factory.feed_service.generate_user_feed(user_id)
"""

from functools import cached_property

from sqlalchemy.orm import Session

from repository.feed_storage import FeedStorage
from repository.interest_storage import InterestStorage
from repository.like_history_storage import LikeHistoryStorage
from repository.run_storage import RunStorage
from repository.source_storage import SourceStorage
from repository.subscription_storage import SubscriptionStorage
from repository.user_storage import UserStorage
from service.data_extractor import DataExtractor
from service.feed_service import FeedService
from service.ranking_service import RankingService
from service.subscription_service import SubscriptionService
from utils import config


class ServiceFactory:
    """Factory for creating services with all dependencies wired up.

    Usage:
        with get_db_session() as db:
            factory = ServiceFactory(db)
            factory.feed_service.generate_user_feed(user_id)
    """

    def __init__(self, db: Session, openai_key: str | None = None) -> None:
        self.db = db
        self._openai_key = openai_key or config.OPEN_AI_KEY

    # --- Repositories (cached) ---

    @cached_property
    def user_storage(self) -> UserStorage:
        return UserStorage(self.db)

    @cached_property
    def source_storage(self) -> SourceStorage:
        return SourceStorage(self.db)

    @cached_property
    def subscription_storage(self) -> SubscriptionStorage:
        return SubscriptionStorage(self.db)

    @cached_property
    def feed_storage(self) -> FeedStorage:
        return FeedStorage(self.db)

    @cached_property
    def interest_storage(self) -> InterestStorage:
        return InterestStorage(self.db)

    @cached_property
    def like_history_storage(self) -> LikeHistoryStorage:
        return LikeHistoryStorage(self.db)

    @cached_property
    def run_storage(self) -> RunStorage:
        return RunStorage(self.db)

    # --- Services (cached) ---

    @cached_property
    def data_extractor(self) -> DataExtractor:
        return DataExtractor(self._openai_key)

    @cached_property
    def ranking_service(self) -> RankingService:
        return RankingService(
            self.interest_storage,
            self.like_history_storage,
        )

    @cached_property
    def feed_service(self) -> FeedService:
        return FeedService(
            self.feed_storage,
            self.subscription_storage,
            self.source_storage,
            self.data_extractor,
            self.ranking_service,
            self.like_history_storage,
        )

    @cached_property
    def subscription_service(self) -> SubscriptionService:
        return SubscriptionService(
            self.feed_storage,
            self.subscription_storage,
            self.source_storage,
        )
