from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class FeedItemBase(BaseModel):
    id: Optional[int] = None
    source_id: int
    title: str
    link: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    published: Optional[datetime] = None
    hn_id: str
    description: str
    comments_link: str
    article_url: str
    comments_url: str
    points: int
    num_comments: int


class FeedItemCreate(FeedItemBase):
    pass


class FeedItemUpdate(FeedItemBase):
    id: int

    pass


class FeedItemSchema(FeedItemBase):
    id: int

    class Config:
        orm_mode = True


class RunBase(BaseModel):
    subscription_id: int
    status: str


class RunCreate(RunBase):
    pass


class RunUpdate(RunBase):
    pass


class RunSchema(RunBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True


class SourceBase(BaseModel):
    name: str
    resource_url: str
    is_active: Optional[bool] = True


class SourceCreate(SourceBase):
    pass


class SourceUpdate(SourceBase):
    pass


class SourceSchema(SourceBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True


class SubscriptionBase(BaseModel):
    is_active: Optional[bool] = True
    user_id: int
    source_id: Optional[int] = None


class SubscriptionCreate(SubscriptionBase):
    resource_url: str


class SubscriptionUpdate(SubscriptionBase):
    pass


class SubscriptionSchema(SubscriptionBase):
    id: int
    created_at: datetime
    source: SourceSchema
    last_run: Optional[datetime] = None

    class Config:
        orm_mode = True
