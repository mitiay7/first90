import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

os.environ["DATABASE_URL"] = "sqlite:///./data/test-first90.db"
os.environ["OPENAI_API_KEY"] = ""
os.environ["DEMO_MODE"] = "true"

from app.db import Base, SessionFactory, engine
from app.main import app
from app.seed import seed_database


@pytest.fixture(autouse=True)
def clean_database() -> Generator[None, None, None]:
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with SessionFactory() as session:
        seed_database(session)
    yield


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client
