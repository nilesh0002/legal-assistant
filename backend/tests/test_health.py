"""
M0 smoke tests.

Run with:  pytest tests/ -v
"""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_health_returns_200():
    """The /health endpoint should return 200 with status 'healthy'."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "Indian Legal Knowledge Assistant"
    assert data["version"] == "0.1.0"
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_health_has_valid_timestamp():
    """The timestamp should be a valid ISO format string."""
    from datetime import datetime

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")

    data = response.json()
    # This will raise ValueError if the format is wrong
    parsed = datetime.fromisoformat(data["timestamp"])
    assert parsed is not None


@pytest.mark.asyncio
async def test_nonexistent_endpoint_returns_404():
    """Endpoints that don't exist should return 404, not 500."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/nonexistent")

    assert response.status_code == 404
