"""pytest configuration for the backend test suite.

Strategy
--------
Tests run against an in-memory SQLite database — no Postgres needed in CI.
We override the ``DATABASE_URL`` and ``JWT_SECRET`` environment variables
*before* importing any app modules, because Pydantic Settings reads env vars
at class-definition time (module import), not at call time.
"""

import os

# ── Set env vars FIRST — must happen before any ``from app.xxx import ...`` ──
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-not-for-production")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:5173")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402

# ── Isolated SQLite engine for tests ─────────────────────────────────────────
_TEST_DB_URL = "sqlite:///./test.db"
_engine = create_engine(_TEST_DB_URL, connect_args={"check_same_thread": False})
_TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


def _override_get_db():
    db = _TestingSession()
    try:
        yield db
    finally:
        db.close()


# Replace the production DB dependency with the test one globally
app.dependency_overrides[get_db] = _override_get_db


@pytest.fixture(autouse=True)
def _reset_database():
    """Create all tables before each test, drop them after."""
    Base.metadata.create_all(bind=_engine)
    yield
    Base.metadata.drop_all(bind=_engine)


@pytest.fixture()
def client() -> TestClient:
    """Return a synchronous HTTPX test client for the FastAPI app."""
    with TestClient(app) as c:
        yield c
