"""Unit tests for API endpoints."""

import uuid
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from src.thematic_lm.api.main import app
from src.thematic_lm.models.database import Analysis, AnalysisStatus


@pytest.fixture
def mock_db_session() -> AsyncMock:
    """Create a mock database session."""
    session = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.execute = AsyncMock()
    return session


@pytest.fixture
def mock_settings() -> MagicMock:
    """Create mock settings."""
    settings = MagicMock()
    settings.COST_BUDGET_USD = 5.0
    settings.IDENTITIES_PATH = "identities.yaml"
    settings.LOG_LEVEL = "INFO"
    return settings


@pytest.mark.asyncio
async def test_health_endpoint() -> None:
    """Test health check endpoint returns 200."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


@pytest.mark.asyncio
async def test_request_id_in_response() -> None:
    """Test that X-Request-Id is returned in response headers."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
        assert "X-Request-Id" in response.headers


@pytest.mark.asyncio
async def test_request_id_preserved() -> None:
    """Test that provided X-Request-Id is preserved."""
    request_id = str(uuid.uuid4())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health", headers={"X-Request-Id": request_id})
        assert response.headers["X-Request-Id"] == request_id


@pytest.mark.asyncio
async def test_create_analysis_returns_202(mock_db_session: AsyncMock, mock_settings: MagicMock) -> None:
    """Test POST /analyze returns 202 with analysis_id."""
    from datetime import datetime
    from src.thematic_lm.api.dependencies import get_db, get_settings_dependency, get_current_user
    
    async def mock_get_db():
        yield mock_db_session
    
    # Mock database query for idempotency check
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db_session.execute.return_value = mock_result
    
    # Mock the refresh method to set created_at
    async def mock_refresh(obj):
        obj.created_at = datetime.utcnow()
    
    mock_db_session.refresh = AsyncMock(side_effect=mock_refresh)

    # Override dependencies
    app.dependency_overrides[get_db] = mock_get_db
    app.dependency_overrides[get_settings_dependency] = lambda: mock_settings
    app.dependency_overrides[get_current_user] = lambda: {"tenant_id": str(uuid.uuid4())}

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/analyze",
                json={
                    "account_id": str(uuid.uuid4()),
                    "start_date": "2024-01-01",
                    "end_date": "2024-01-31",
                },
                headers={"Authorization": "Bearer test-token"},
            )

            assert response.status_code == 202
            data = response.json()
            assert "analysis_id" in data
            assert data["status"] == "pending"
            assert "estimated_cost_usd" in data
            assert "created_at" in data
    finally:
        # Clean up overrides
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_analysis_invalid_date_range(mock_db_session: AsyncMock, mock_settings: MagicMock) -> None:
    """Test POST /analyze returns 400 for invalid date range."""
    from src.thematic_lm.api.dependencies import get_db, get_settings_dependency, get_current_user
    
    async def mock_get_db():
        yield mock_db_session
    
    # Override dependencies
    app.dependency_overrides[get_db] = mock_get_db
    app.dependency_overrides[get_settings_dependency] = lambda: mock_settings
    app.dependency_overrides[get_current_user] = lambda: {"tenant_id": str(uuid.uuid4())}

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/analyze",
                json={
                    "account_id": str(uuid.uuid4()),
                    "start_date": "2024-01-31",
                    "end_date": "2024-01-01",  # End before start
                },
                headers={"Authorization": "Bearer test-token"},
            )

            assert response.status_code == 400
            data = response.json()
            assert "error" in data["detail"]
            assert data["detail"]["error"]["code"] == "INVALID_DATE_RANGE"
    finally:
        # Clean up overrides
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_analysis_not_found(mock_db_session: AsyncMock) -> None:
    """Test GET /analysis/{id} returns 404 for non-existent analysis."""
    from src.thematic_lm.api.dependencies import get_db, get_current_user
    
    async def mock_get_db():
        yield mock_db_session
    
    # Mock database query returning None
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db_session.execute.return_value = mock_result

    # Override dependencies
    app.dependency_overrides[get_db] = mock_get_db
    app.dependency_overrides[get_current_user] = lambda: {"tenant_id": str(uuid.uuid4())}

    try:
        analysis_id = uuid.uuid4()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                f"/analysis/{analysis_id}",
                headers={"Authorization": "Bearer test-token"},
            )

            assert response.status_code == 404
            data = response.json()
            assert "error" in data["detail"]
            assert data["detail"]["error"]["code"] == "NOT_FOUND"
    finally:
        # Clean up overrides
        app.dependency_overrides.clear()
