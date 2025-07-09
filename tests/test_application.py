# Test Configuration and Sample Test Files
# This file creates the test directory structure and sample tests

import asyncio
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture  # type: ignore[misc]
def client() -> TestClient:
    """Create a test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture  # type: ignore[misc]
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


class TestApplicationHealth:
    """Test application health checks and basic functionality."""

    def test_health_check(self, client: TestClient) -> None:
        """Test the basic health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "ManipulatorAI"
        assert "version" in data
        assert "timestamp" in data

    def test_root_endpoint(self, client: TestClient) -> None:
        """Test the root endpoint returns service information."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "ManipulatorAI"
        assert "version" in data
        assert "description" in data

    def test_detailed_health_check(self, client: TestClient) -> None:
        """Test the detailed health check endpoint."""
        response = client.get("/health/detailed")
        assert response.status_code in [200, 503]  # 503 if services are down
        data = response.json()
        assert "status" in data
        assert "checks" in data
        assert "application" in data["checks"]


class TestCoreConfiguration:
    """Test core configuration functionality."""

    def test_settings_import(self) -> None:
        """Test that settings can be imported and initialized."""
        from src.core.config import get_settings

        settings = get_settings()
        assert settings.app_name == "ManipulatorAI"
        assert settings.environment in ["development", "testing", "staging", "production"]
        assert isinstance(settings.debug, bool)

    def test_logging_setup(self) -> None:
        """Test that logging can be set up without errors."""
        from src.core.logging_config import get_logger, setup_logging

        # This should not raise any exceptions
        setup_logging()
        logger = get_logger(__name__)
        assert logger is not None


# Integration tests (marked as slow)
@pytest.mark.slow
class TestApplicationIntegration:
    """Integration tests for the full application."""

    @pytest.mark.asyncio  # type: ignore[misc]
    async def test_application_startup(self) -> None:
        """Test that the application can start up successfully."""
        # This would test actual startup with real dependencies
        # For now, we just test that imports work
        from src.main import create_application

        app = create_application()
        assert app is not None
        assert len(app.routes) > 0
