"""Shared test fixtures and configuration."""
import os
from collections.abc import AsyncGenerator

import pytest
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.database.base import Base
from app.database.connection import get_db
from app.main import create_application

# Check if PostgreSQL is available for integration tests
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")

# Mark all database tests as requiring PostgreSQL
pytestmark = pytest.mark.skipif(
    not TEST_DATABASE_URL,
    reason="PostgreSQL not available - set TEST_DATABASE_URL to run database integration tests",
)


async def _create_tables(engine) -> None:
    """Create all tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def _drop_tables(engine) -> None:
    """Drop all tables with CASCADE to handle foreign keys."""
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "DROP TABLE IF EXISTS "
                "roadmap_tasks, messages, roadmaps, uploaded_documents, "
                "eligibility_results, recommendations, conversations, "
                "refresh_tokens, business_profiles, users CASCADE"
            )
        )


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a database session for testing."""
    if not TEST_DATABASE_URL:
        pytest.skip("PostgreSQL not available")

    engine = create_async_engine(TEST_DATABASE_URL, poolclass=None)
    await _create_tables(engine)

    from sqlalchemy.ext.asyncio import async_sessionmaker
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        try:
            yield session
        finally:
            await session.rollback()
            await session.close()

    await _drop_tables(engine)
    await engine.dispose()


@pytest.fixture
def app():
    """Create a test application instance."""
    return create_application()


@pytest.fixture
async def client(app, db_session) -> AsyncGenerator:
    """Create an async test client with database dependency override."""
    from app.main import app as main_app

    # Override the get_db dependency to use the test session
    def override_get_db():
        yield db_session

    main_app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=main_app, base_url="http://test") as ac:
        yield ac

    # Clean up
    main_app.dependency_overrides.clear()
