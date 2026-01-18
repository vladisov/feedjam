"""FastAPI dependency injection.

Usage in routers:
    @router.get("/feed/{user_id}")
    def get_feed(feed_service: FeedService = Depends(get_feed_service)):
        ...
"""

from fastapi import Depends
from sqlalchemy.orm import Session

from repository.db import get_db
from service.factory import ServiceFactory


def get_factory(db: Session = Depends(get_db)) -> ServiceFactory:
    """Create a ServiceFactory for the current request."""
    return ServiceFactory(db)


# Convenience shortcuts for common dependencies
def get_user_storage(factory: ServiceFactory = Depends(get_factory)):
    return factory.user_storage


def get_source_storage(factory: ServiceFactory = Depends(get_factory)):
    return factory.source_storage


def get_subscription_storage(factory: ServiceFactory = Depends(get_factory)):
    return factory.subscription_storage


def get_feed_storage(factory: ServiceFactory = Depends(get_factory)):
    return factory.feed_storage


def get_interest_storage(factory: ServiceFactory = Depends(get_factory)):
    return factory.interest_storage


def get_run_storage(factory: ServiceFactory = Depends(get_factory)):
    return factory.run_storage


def get_feed_service(factory: ServiceFactory = Depends(get_factory)):
    return factory.feed_service


def get_subscription_service(factory: ServiceFactory = Depends(get_factory)):
    return factory.subscription_service
