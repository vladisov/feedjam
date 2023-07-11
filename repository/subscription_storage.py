
from typing import List, Optional
from sqlalchemy.orm import Session
from model.model import Subscription
from sqlalchemy import or_, func


from model.schema.feed_schema import SourceSchema, SubscriptionCreate, SubscriptionSchema, SubscriptionUpdate


class SubscriptionStorage:
    def __init__(self, db: Session):
        self.db = db

    def get_subscription(self, subscription_id: int) -> Optional[SubscriptionSchema]:
        return self.db.query(Subscription).filter(Subscription.id == subscription_id).first()

    def get_subscriptions(self, skip: int = 0, limit: int = 100):
        return self.db.query(Subscription).offset(skip).limit(limit).all()

    def get_user_subscriptions(self, user_id: int) -> List[SubscriptionSchema]:
        return self.db.query(Subscription).filter(Subscription.user_id == user_id).all()

    def get_subscriptions_to_run(self) -> List[SubscriptionSchema]:
        subscriptions = (
            self.db.query(Subscription)
            .filter(
                Subscription.is_active,
                or_(
                    Subscription.last_run.is_(None),
                    Subscription.last_run < func.datetime('now', '-1 hour')
                )
            )
            .all()
        )

        return [SubscriptionSchema.from_orm(sub) for sub in subscriptions]

    def create_subscription(self, subscription: SubscriptionCreate) -> SubscriptionSchema:
        db_subscription = self.db.query(Subscription).filter(
            (Subscription.user_id == subscription.user_id) &
            (Subscription.source_id == subscription.source_id)
        ).first()

        if db_subscription is None:
            db_subscription = Subscription(
                user_id=subscription.user_id, source_id=subscription.source_id, is_active=True)
            self.db.add(db_subscription)
            self.db.commit()
            self.db.refresh(db_subscription)

        db_subscription_dict = db_subscription.__dict__
        db_source_dict = db_subscription.source.__dict__

        return SubscriptionSchema(
            id=db_subscription_dict["id"],
            user_id=db_subscription_dict["user_id"],
            is_active=db_subscription_dict["is_active"],
            created_at=db_subscription_dict["created_at"],
            source_id=db_subscription_dict["source_id"],
            source=SourceSchema(**db_source_dict)
        )

    def update_subscription(self, subscription: SubscriptionUpdate, subscription_id: int):
        db_subscription = self.get_subscription(subscription_id)
        if db_subscription is None:
            return None
        for var, value in vars(subscription).items():
            setattr(db_subscription, var, value) if value else None
        self.db.commit()
        self.db.refresh(db_subscription)
        return db_subscription

    def delete_subscription(self, subscription_id: int):
        db_subscription = self.get_subscription(subscription_id)
        if db_subscription is None:
            return None
        self.db.delete(db_subscription)
        self.db.commit()
        return {"message": "Subscription deleted"}
