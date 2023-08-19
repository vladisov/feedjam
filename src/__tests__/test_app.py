import pytest
from starlette.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from model.schema.user_schema import UserSchema

from repository.db import get_db
from src.main import app

SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()  # type: ignore


app.dependency_overrides[get_db] = override_get_db  # type: ignore
client = TestClient(app)


def _create_user(handle: str):
    response = client.post(
        "/users/",
        json={"handle": handle},
    )
    return UserSchema(**response.json())


@pytest.mark.parametrize("handle", ["yam"])
def test_create_user(handle, cleanup):
    user = _create_user(handle)

    assert user.handle == handle
    assert user.is_active
