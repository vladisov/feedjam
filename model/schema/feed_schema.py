from pydantic import BaseModel
from typing import ForwardRef, Optional, List
from datetime import datetime

UserFeedItemCreateRef = ForwardRef('UserFeedItemCreate')
UserFeedItemSchemaRef = ForwardRef('UserFeedItemSchema')


class FeedBase(BaseModel):
    source_id: int


class FeedCreate(FeedBase):
    pass


class FeedUpdate(FeedBase):
    pass


class FeedSchema(FeedBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


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
    summary: Optional[str] = None


class FeedItemCreate(FeedItemBase):
    pass


class FeedItemUpdate(FeedItemBase):
    id: int

    pass


class FeedItemSchema(FeedItemBase):
    id: int
    user_feed_items: Optional[List[UserFeedItemSchemaRef]]  # type: ignore

    class Config:
        orm_mode = True


class UserFeedBase(BaseModel):
    user_id: int
    is_active: Optional[bool] = True


class UserFeedCreate(UserFeedBase):
    user_feed_items: List[UserFeedItemCreateRef]  # type: ignore


class UserFeedUpdate(UserFeedBase):
    pass


class UserFeedSchema(UserFeedBase):
    id: int
    created_at: datetime
    updated_at: datetime
    user_feed_items: List[UserFeedItemCreateRef]  # type: ignore

    class Config:
        orm_mode = True


class StateBase(BaseModel):
    hide: Optional[bool] = None
    read: Optional[bool] = None
    star: Optional[bool] = None
    like: Optional[bool] = None
    dislike: Optional[bool] = None


class UserFeedItemBase(BaseModel):
    feed_item_id: int
    user_id: int
    state: StateBase


class UserFeedItemCreate(UserFeedItemBase):
    pass


class UserFeedItemUpdate(UserFeedItemBase):
    pass


class UserFeedItemSchema(UserFeedItemBase):
    id: int
    created_at: datetime
    updated_at: datetime
    summary: Optional[str] = None
    source_name: Optional[str] = None

    class Config:
        orm_mode = True


class UserBase(BaseModel):
    handle: str
    is_active: Optional[bool] = True


class UserCreate(UserBase):
    pass


class UserUpdate(UserBase):
    pass


class UserSchema(UserBase):
    id: int
    created_at: datetime
    user_feeds: List[UserFeedSchema]
    user_feed_items: List[UserFeedItemSchema]

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
    feeds: Optional[List[FeedSchema]]
    feed_items: Optional[List[FeedItemSchema]]

    class Config:
        orm_mode = True


class SubscriptionBase(BaseModel):
    is_active: Optional[bool] = True
    source_id: Optional[int] = None


class SubscriptionCreate(SubscriptionBase):
    resource_url: str
    user_id: int


class SubscriptionUpdate(SubscriptionBase):
    last_run: Optional[datetime] = None


class SubscriptionSchema(SubscriptionBase):
    id: int
    user_id: int
    created_at: datetime
    source: SourceSchema
    last_run: Optional[datetime] = None
    runs: Optional[List[RunSchema]]

    class Config:
        orm_mode = True


FeedItemSchema.update_forward_refs()
UserFeedCreate.update_forward_refs()
UserFeedSchema.update_forward_refs()
