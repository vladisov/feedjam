from typing import ForwardRef, Optional, List
from datetime import datetime
from pydantic import BaseModel


UserFeedItemCreateRef = ForwardRef('UserFeedItemCreate')
UserFeedItemSchemaRef = ForwardRef('UserFeedItemSchema')
FeedItemSchemaRef = ForwardRef('FeedItemSchema')


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
    feed_items: Optional[List[FeedItemSchemaRef]] = []  # type: ignore

    class Config:
        orm_mode = True


class FeedItemBase(BaseModel):
    id: Optional[int] = None
    title: str
    link: str
    source_name: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    published: Optional[datetime] = None
    local_id: Optional[str] = None
    description: str
    article_url: Optional[str] = None
    comments_url: Optional[str] = None
    points: Optional[int] = None
    views: Optional[int] = None
    num_comments: int
    summary: Optional[str] = None


class FeedItemCreate(FeedItemBase):
    pass


class FeedItemUpdate(FeedItemBase):
    id: int


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
    user_feed_items: List[UserFeedItemSchemaRef]  # type: ignore

    class Config:
        orm_mode = True


class StateBase(BaseModel):
    hide: Optional[bool] = None
    read: Optional[bool] = None
    star: Optional[bool] = None
    like: Optional[bool] = None
    dislike: Optional[bool] = None

    class Config:
        orm_mode = True


class UserFeedItemBase(BaseModel):
    feed_item_id: int
    user_id: int
    state: StateBase
    source_name: str


class UserFeedItemCreate(UserFeedItemBase):
    description: str
    title: str
    article_url: Optional[str] = None
    comments_url: Optional[str] = None
    points: Optional[int] = None
    views: Optional[int] = None
    summary: Optional[str] = None


class UserFeedItemUpdate(UserFeedItemBase):
    pass


class UserFeedItemSchema(UserFeedItemBase):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime
    summary: Optional[str] = None
    source_name: Optional[str] = None
    description: str
    article_url: Optional[str] = None
    comments_url: Optional[str] = None
    points: Optional[int] = None
    views: Optional[int] = None

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
    user_feeds: Optional[List[UserFeedSchema]] = []
    user_feed_items: Optional[List[UserFeedItemSchema]] = []

    class Config:
        orm_mode = True


class RunBase(BaseModel):
    status: str
    job_type: str
    subscription_id: Optional[int] = None
    user_id: Optional[int] = None


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


class SubscriptionCreateAPI(SubscriptionBase):
    resource_url: str
    user_id: int


class SubscriptionCreate(SubscriptionBase):
    resource_url: str
    user_id: int
    source_id: Optional[int] = None


class SubscriptionUpdate(SubscriptionBase):
    id: int
    last_run: Optional[datetime] = None


class SubscriptionSchema(SubscriptionBase):
    id: int
    user_id: int
    created_at: datetime
    last_run: Optional[datetime] = None
    runs: Optional[List[RunSchema]]
    source_name: Optional[str] = None
    source_id: int

    class Config:
        orm_mode = True


FeedItemSchema.update_forward_refs()
UserFeedCreate.update_forward_refs()
UserFeedSchema.update_forward_refs()
FeedSchema.update_forward_refs()
