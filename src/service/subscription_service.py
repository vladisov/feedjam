"""Subscription service - handles subscription management."""

from model.source import SourceType
from repository.feed_storage import FeedStorage
from repository.source_storage import SourceStorage
from repository.subscription_storage import SubscriptionStorage
from schemas import SourceIn, SubscriptionIn, SubscriptionOut
from schemas.subscriptions import SubscriptionCreateIn
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

    def _create_subscription(self, resource_url: str, user_id: int) -> SubscriptionOut:
        """Internal method to create a subscription."""
        # Auto-detect source type from URL
        source_type = detect_source_type(resource_url) or SourceType.RSS.value

        # Generate source name
        source_name = parse_source_name(resource_url, source_type)

        # Get or create source
        source = self.source_storage.create(
            SourceIn(
                name=source_name,
                resource_url=resource_url,
                source_type=source_type,
            )
        )

        # Create subscription
        result = self.subscription_storage.create(user_id, source.id)
        logger.debug("Created subscription: %s", result)
        return result

    def create(self, subscription: SubscriptionIn) -> SubscriptionOut:
        """Create a new subscription (legacy method with user_id in body)."""
        return self._create_subscription(subscription.resource_url, subscription.user_id)

    def create_for_user(self, subscription: SubscriptionCreateIn, user_id: int) -> SubscriptionOut:
        """Create a new subscription for the authenticated user."""
        return self._create_subscription(subscription.resource_url, user_id)

    def get(self, subscription_id: int) -> SubscriptionOut | None:
        """Get a subscription by ID."""
        subscription = self.subscription_storage.get(subscription_id)
        if subscription:
            return SubscriptionOut.model_validate(subscription)
        return None

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
