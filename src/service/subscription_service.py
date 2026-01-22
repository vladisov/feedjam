"""Subscription service - handles subscription management."""

from model.source import SourceType
from repository.feed_storage import FeedStorage
from repository.source_storage import SourceStorage
from repository.subscription_storage import SubscriptionStorage
from schemas import SourceIn, SubscriptionIn, SubscriptionOut
from schemas.subscriptions import FeedPreviewItem, FeedPreviewOut, SubscriptionCreateIn
from service.parser import detect_source_type, parse_source_name
from service.parser.base import get_parser
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
        logger.info(
            f"Creating subscription: user={user_id} url={resource_url} detected_type={source_type}"
        )

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
        logger.info(
            f"Subscription created: user={user_id} subscription={result.id} "
            f"source={source_name} type={source_type}"
        )
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

    def get_owner_id(self, subscription_id: int) -> int | None:
        """Get the owner user_id for a subscription. Used for ownership verification."""
        subscription = self.subscription_storage.get(subscription_id)
        return subscription.user_id if subscription else None

    def get_by_user(self, user_id: int) -> list[SubscriptionOut]:
        """Get all subscriptions for a user.

        Source info (name, type, URL) is populated via Subscription model properties.
        """
        return self.subscription_storage.get_by_user(user_id)

    def get_all(self) -> list[SubscriptionOut]:
        """Get all active subscriptions."""
        return [SubscriptionOut.model_validate(s) for s in self.subscription_storage.get_active()]

    def delete(self, subscription_id: int, user_id: int | None = None) -> bool:
        """Delete a subscription."""
        result = self.subscription_storage.delete(subscription_id)
        if result:
            logger.info(f"Deleted subscription: user={user_id} subscription={subscription_id}")
        else:
            logger.warning(f"Subscription not found: user={user_id} subscription={subscription_id}")
        return result

    def preview_feed(self, resource_url: str) -> FeedPreviewOut:
        """Preview a feed URL without subscribing."""
        from model.source import Source

        source_type = detect_source_type(resource_url) or SourceType.RSS.value
        source_name = parse_source_name(resource_url, source_type)

        def make_error_response(error: str) -> FeedPreviewOut:
            return FeedPreviewOut(
                source_type=source_type,
                source_name=source_name,
                item_count=0,
                items=[],
                error=error,
            )

        parser = get_parser(source_type)
        if not parser:
            return make_error_response(f"No parser available for source type: {source_type}")

        try:
            mock_source = Source(
                id=0,
                name=source_name,
                resource_url=resource_url,
                source_type=source_type,
            )
            items = parser.parse(mock_source)

            preview_items = [
                FeedPreviewItem(
                    title=item.title,
                    link=item.link,
                    published=item.published,
                    description=item.description[:200] if item.description else None,
                )
                for item in items[:10]
            ]

            return FeedPreviewOut(
                source_type=source_type,
                source_name=source_name,
                item_count=len(items),
                items=preview_items,
            )

        except Exception as e:
            logger.exception("Error previewing feed: %s", resource_url)
            return make_error_response(str(e))
