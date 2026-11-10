"""Tests for health endpoints and application startup."""
from collections.abc import AsyncGenerator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError

from app.core.config import Settings
from app.main import create_application


@pytest.fixture
def app() -> FastAPI:
    """Create a test application instance."""
    return create_application()


@pytest.fixture
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestApplicationStartup:
    """Tests for application startup and basic functionality."""

    @pytest.mark.asyncio
    async def test_app_creation(self, app: FastAPI) -> None:
        """Test that the application creates successfully."""
        assert app is not None
        assert app.title == "SarkarSetu AI"
        assert app.version == "1.0.0"

    @pytest.mark.asyncio
    async def test_root_endpoint(self, client: AsyncClient) -> None:
        """Test the root endpoint returns correct response."""
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Welcome to SarkarSetu AI"
        assert data["version"] == "1.0.0"
        assert data["docs"] == "/docs"

    @pytest.mark.asyncio
    async def test_docs_endpoint(self, client: AsyncClient) -> None:
        """Test that the docs endpoint is accessible."""
        response = await client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    @pytest.mark.asyncio
    async def test_health_endpoint(self, client: AsyncClient) -> None:
        """Test the health check endpoint returns expected structure."""
        response = await client.get("/api/v1/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert data["application"] == "SarkarSetu AI"
        assert data["version"] == "1.0.0"
        # Ensure no sensitive data is exposed
        assert "database_url" not in str(data)
        assert "api_key" not in str(data).lower()
        assert "secret" not in str(data).lower()

    @pytest.mark.asyncio
    async def test_health_endpoint_structure(self, client: AsyncClient) -> None:
        """Test health endpoint response has exactly the expected fields."""
        response = await client.get("/api/v1/health")
        data = response.json()

        expected_keys = {"status", "application", "version"}
        assert set(data.keys()) == expected_keys

    @pytest.mark.asyncio
    async def test_database_health_endpoint(self, client: AsyncClient) -> None:
        """Test database health check endpoint exists."""
        response = await client.get("/api/v1/health/db")
        # May return 200 or 503 depending on DB availability
        assert response.status_code in (200, 503)
        data = response.json()
        assert "status" in data
        assert "database" in data


class TestConfiguration:
    """Tests for configuration loading."""

    def test_settings_load_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test settings are loaded from environment variables."""
        monkeypatch.setenv("APP_NAME", "Test App")
        monkeypatch.setenv("ENVIRONMENT", "testing")
        monkeypatch.setenv("DEBUG", "true")
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test")
        monkeypatch.setenv("GEMINI_API_KEY", "test-key")
        monkeypatch.setenv("JWT_SECRET", "test-secret")

        # Need to clear the lru_cache
        from app.core.config import get_settings
        get_settings.cache_clear()

        settings = get_settings()

        assert settings.app_name == "Test App"
        assert settings.environment == "testing"
        assert settings.debug is True
        assert settings.database_url == "postgresql+asyncpg://test:test@localhost/test"
        assert settings.gemini_api_key == "test-key"
        assert settings.jwt_secret == "test-secret"

    def test_settings_defaults(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test settings have correct defaults when not provided."""
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test")
        monkeypatch.setenv("GEMINI_API_KEY", "test-key")
        monkeypatch.setenv("JWT_SECRET", "test-secret")
        monkeypatch.setenv("CORS_ORIGINS", '["http://localhost:3000"]')

        from app.core.config import get_settings
        get_settings.cache_clear()

        settings = get_settings()

        assert settings.api_prefix == "/api/v1"
        assert settings.jwt_algorithm == "HS256"
        assert settings.access_token_expire_minutes == 30
        assert settings.cors_origins == ["http://localhost:3000"]

    def test_settings_is_development_property(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test is_development property works correctly."""
        monkeypatch.setenv("ENVIRONMENT", "development")
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test")
        monkeypatch.setenv("GEMINI_API_KEY", "test-key")
        monkeypatch.setenv("JWT_SECRET", "test-secret")

        from app.core.config import get_settings
        get_settings.cache_clear()

        settings = get_settings()
        assert settings.is_development is True
        assert settings.is_production is False

    def test_settings_is_production_property(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test is_production property works correctly."""
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test")
        monkeypatch.setenv("GEMINI_API_KEY", "test-key")
        monkeypatch.setenv("JWT_SECRET", "test-secret")

        from app.core.config import get_settings
        get_settings.cache_clear()

        settings = get_settings()
        assert settings.is_development is False
        assert settings.is_production is True


class TestMissingConfiguration:
    """Tests for missing environment configuration behavior."""

    def test_missing_database_url_raises_error(self, tmp_path: str, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that missing DATABASE_URL raises validation error."""
        # Change to temp directory without .env file
        monkeypatch.chdir(tmp_path)

        with pytest.raises(ValidationError):
            Settings(  # type: ignore[call-arg]
                app_name="Test",
                environment="testing",
                gemini_api_key="test-key",
                jwt_secret="test-secret",
                # database_url not provided - should fail
            )

    def test_missing_gemini_key_raises_error(self, tmp_path: str, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that missing GEMINI_API_KEY raises validation error."""
        monkeypatch.chdir(tmp_path)

        with pytest.raises(ValidationError):
            Settings(  # type: ignore[call-arg]
                app_name="Test",
                environment="testing",
                database_url="postgresql+asyncpg://test:test@localhost/test",
                jwt_secret="test-secret",
                # gemini_api_key not provided - should fail
            )

    def test_missing_jwt_secret_raises_error(self, tmp_path: str, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that missing JWT_SECRET raises validation error."""
        monkeypatch.chdir(tmp_path)

        with pytest.raises(ValidationError):
            Settings(  # type: ignore[call-arg]
                app_name="Test",
                environment="testing",
                database_url="postgresql+asyncpg://test:test@localhost/test",
                gemini_api_key="test-key",
                # jwt_secret not provided - should fail
            )
