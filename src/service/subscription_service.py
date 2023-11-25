
from typing import List

from model.schema.feed_schema import SourceCreate, SubscriptionCreate, SubscriptionCreateAPI, SubscriptionSchema
from repository.feed_storage import FeedStorage
from repository.source_storage import SourceStorage
from repository.subscription_storage import SubscriptionStorage
from service.parser.source_parser_strategy import parse_name
from utils.logger import get_logger

logger = get_logger(__name__)


class SubscriptionService:

    def __init__(self, feed_storage: FeedStorage,
                 subscription_storage: SubscriptionStorage,
                 source_storage: SourceStorage):
        self.running_subscriptions = {}
        self.feed_storage = feed_storage
        self.subscription_storage = subscription_storage
        self.source_storage = source_storage

    def add_subscription(self, subscription_create: SubscriptionCreateAPI) -> SubscriptionSchema:
        # Prepare the source based on the resource_url from the incoming subscription
        source_name = parse_name(subscription_create.resource_url)
        source_create = SourceCreate(
            resource_url=subscription_create.resource_url, name=source_name)

        # Fetch the source based on the resource_url or create it if it does not exist
        source = self.source_storage.create_source(source_create)

        # Set source_id in the subscription object
        subscription_schema = SubscriptionCreate(**subscription_create.dict())
        subscription_schema.source_id = source.id

        # Add the subscription
        created_subscription = self.subscription_storage.create_subscription(
            subscription_schema)

        logger.debug("Created subscription: %s", created_subscription)

        return created_subscription

    def get_all_subscriptions(self) -> List[SubscriptionSchema]:
        return self.subscription_storage.get_subscriptions()

    def get_user_subscriptions(self, user_id: int) -> List[SubscriptionSchema]:
        return self.subscription_storage.get_user_subscriptions(user_id)
