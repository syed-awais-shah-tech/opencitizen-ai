"""Pytest fixtures and configuration for backend test suite."""

from collections.abc import Generator

import pytest
from app.core.config import settings
from app.db.session import get_db
from app.main import app
from app.models.base import Base
from app.search.dependencies import get_vector_store_instance
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# Configure hermetic in-memory environments for tests
settings.QDRANT_IN_MEMORY = True
get_vector_store_instance.cache_clear()

# In-memory SQLite engine for fast, isolated, hermetic unit & integration tests
TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(autouse=True)
def init_test_db() -> Generator[None, None, None]:
    """Create all schema tables before each test and drop them afterwards."""
    from app.search.dependencies import (
        get_bm25_index_instance,
        get_vector_store_instance,
    )
    from app.services.ingestion_worker import ingestion_worker

    get_vector_store_instance.cache_clear()
    get_bm25_index_instance.cache_clear()
    ingestion_worker.set_session_factory(TestingSessionLocal)
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)
    get_vector_store_instance.cache_clear()
    get_bm25_index_instance.cache_clear()


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Provide a clean test database session."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """Provide a TestClient with database dependency overridden for tests."""

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
