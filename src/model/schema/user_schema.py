from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class UserBase(BaseModel):
    handle: str


class UserCreate(UserBase):
    pass


class UserUpdate(UserBase):
    is_active: Optional[bool] = True


class UserSchema(UserBase):
    id: int
    created_at: datetime
    is_active: Optional[bool] = True

    class Config:
        orm_mode = True
