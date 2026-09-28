import os

# Keep the app's own startup hook away from any on-disk database during tests.
os.environ["APP_DATABASE_URL"] = "sqlite://"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.config import Settings, get_settings  # noqa: E402
from app.db import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture
def settings():
    return Settings(api_tokens="ci-agent:test-token", require_auth=False)


@pytest.fixture
def client(settings):
    # A fresh in-memory database per test, shared across connections.
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine, expire_on_commit=False)

    def override_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_settings] = lambda: settings
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def sample():
    return {
        "name": "payments-api",
        "description": "Handles card payments",
        "owner_team": "Payments",
        "owner_email": "payments@example.com",
        "repo_url": "https://github.com/example/payments-api",
        "lifecycle": "active",
    }
