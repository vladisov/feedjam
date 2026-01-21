"""Subscription repository."""

from datetime import timedelta

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from model.subscription import Subscription
from schemas import SubscriptionOut, SubscriptionUpdate


class SubscriptionStorage:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, subscription_id: int) -> Subscription | None:
        """Get a subscription by ID (returns ORM object for service layer)."""
        stmt = select(Subscription).where(Subscription.id == subscription_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_user(self, user_id: int) -> list[SubscriptionOut]:
        """Get all subscriptions for a user."""
        stmt = select(Subscription).where(Subscription.user_id == user_id)
        subscriptions = self.db.execute(stmt).scalars().all()
        return [SubscriptionOut.model_validate(s) for s in subscriptions]

    def get_active(self) -> list[Subscription]:
        """Get all active subscriptions."""
        stmt = select(Subscription).where(Subscription.is_active == True)
        return list(self.db.execute(stmt).scalars().all())

    def get_due_for_run(self) -> list[Subscription]:
        """Get subscriptions that need to be run (not run in last 4 hours)."""
        stmt = select(Subscription).where(
            and_(
                Subscription.is_active == True,
                or_(
                    Subscription.last_run.is_(None),
                    Subscription.last_run < func.now() - timedelta(hours=4),
                ),
            )
        )
        return list(self.db.execute(stmt).scalars().all())

    def create(self, user_id: int, source_id: int) -> SubscriptionOut:
        """Create a new subscription (or return existing)."""
        # Check for existing
        stmt = select(Subscription).where(
            and_(
                Subscription.user_id == user_id,
                Subscription.source_id == source_id,
            )
        )
        existing = self.db.execute(stmt).scalar_one_or_none()
        if existing:
            return SubscriptionOut.model_validate(existing)

        db_subscription = Subscription(user_id=user_id, source_id=source_id)
        self.db.add(db_subscription)
        self.db.commit()
        self.db.refresh(db_subscription)
        return SubscriptionOut.model_validate(db_subscription)

    def update(self, subscription_id: int, update: SubscriptionUpdate) -> SubscriptionOut | None:
        """Update a subscription."""
        subscription = self.get(subscription_id)
        if not subscription:
            return None

        update_data = update.model_dump(exclude_none=True)
        for field, value in update_data.items():
            setattr(subscription, field, value)

        self.db.commit()
        self.db.refresh(subscription)
        return SubscriptionOut.model_validate(subscription)

    def clear_error(self, subscription_id: int) -> None:
        """Clear last_error for a subscription."""
        subscription = self.get(subscription_id)
        if subscription:
            subscription.last_error = None
            self.db.commit()

    def delete(self, subscription_id: int) -> bool:
        """Delete a subscription by ID."""
        subscription = self.get(subscription_id)
        if not subscription:
            return False
        self.db.delete(subscription)
        self.db.commit()
        return True
