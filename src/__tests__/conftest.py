
import pytest
from repository.db import Base
from __tests__.test_app import engine

OPEN_AI_KEY = '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'


@pytest.fixture(scope='function', autouse=True)  # type: ignore
def cleanup():
    # db: Session = SessionLocal()
    Base.metadata.create_all(bind=engine)  # type: ignore

    yield  # this is where the testing happens!

    # db.rollback()
    # db.close()
    Base.metadata.drop_all(bind=engine)  # type: ignore
