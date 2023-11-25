
import pytest
from repository.db import Base
from __tests__.test_app import engine


@pytest.fixture(scope='function', autouse=True)  # type: ignore
def cleanup():
    # db: Session = SessionLocal()
    Base.metadata.create_all(bind=engine)  # type: ignore

    yield  # this is where the testing happens!

    # db.rollback()
    # db.close()
    Base.metadata.drop_all(bind=engine)  # type: ignore
