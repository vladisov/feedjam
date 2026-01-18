"""Subscription service - handles subscription management."""

from model.source import SourceType
from repository.feed_storage import FeedStorage
from repository.source_storage import SourceStorage
from repository.subscription_storage import SubscriptionStorage
from schemas import SourceIn, SubscriptionIn, SubscriptionOut
from service.parser import detect_source_type, parse_source_name
from utils.logger import get_logger

logger = get_logger(__name__)


class SubscriptionService:
    def __init__(
        self,
        feed_storage: FeedStorage,
        subscription_storage: SubscriptionStorage,
        source_storage: SourceStorage,
    ) -> None:
        self.feed_storage = feed_storage
        self.subscription_storage = subscription_storage
        self.source_storage = source_storage

    def create(self, subscription: SubscriptionIn) -> SubscriptionOut:
        """Create a new subscription."""
        # Auto-detect source type from URL
        source_type = detect_source_type(subscription.resource_url) or SourceType.RSS.value

        # Generate source name
        source_name = parse_source_name(subscription.resource_url, source_type)

        # Get or create source
        source = self.source_storage.create(
            SourceIn(
                name=source_name,
                resource_url=subscription.resource_url,
                source_type=source_type,
            )
        )

        # Create subscription
        result = self.subscription_storage.create(subscription.user_id, source.id)
        logger.debug("Created subscription: %s", result)
        return result

    def get_by_user(self, user_id: int) -> list[SubscriptionOut]:
        """Get all subscriptions for a user."""
        subscriptions = self.subscription_storage.get_by_user(user_id)

        # Enrich with source name
        for sub in subscriptions:
            source = self.source_storage.get(sub.source_id)
            if source:
                sub.source_name = source.name

        return subscriptions

    def get_all(self) -> list[SubscriptionOut]:
        """Get all active subscriptions."""
        return [SubscriptionOut.model_validate(s) for s in self.subscription_storage.get_active()]

    def delete(self, subscription_id: int) -> bool:
        """Delete a subscription."""
        return self.subscription_storage.delete(subscription_id)
