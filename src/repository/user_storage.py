from typing import List
from sqlalchemy.orm import Session
from model.user import User
from model.schema.user_schema import UserCreate, UserSchema


class UserStorage:

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_user(self, user_id: int) -> UserSchema | None:
        return self.db.query(User).filter(User.id == user_id).first()

    def get_users(self, skip: int = 0, limit: int = 100) -> List[UserSchema]:
        return self.db.query(User).offset(skip).limit(limit).all()

    def get_active_users(self) -> List[UserSchema]:
        return self.db.query(User).filter(User.is_active).all()

    def get_user_by_handle(self, handle: str) -> UserSchema | None:
        return self.db.query(User).filter(User.handle == handle).first()

    def create_user(self, user: UserCreate) -> UserSchema:
        db_user = User(handle=user.handle,
                       is_active=True)
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user
