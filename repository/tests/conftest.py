"""
Shared fixtures for BeeScout backend tests.

Tests use httpx.AsyncClient with the FastAPI app directly — no real MongoDB.
MongoDB calls are mocked at the collection level so tests stay fast and offline.
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport


@pytest.fixture(scope="session")
def mock_collections():
    """Returns mock MongoDB collection objects shared across the session."""
    usr = AsyncMock()
    dgr = AsyncMock()
    return {"usr": usr, "dgr": dgr}


@pytest_asyncio.fixture
async def client(mock_collections):
    """
    HTTP test client with MongoDB collections patched.
    Import app inside fixture so env vars are already set when main.py loads.

    Mocks are session-scoped for speed, but per-test side_effect / return_value
    bleed between tests would cause order-dependent failures (issue #39).
    Reset both before each test to guarantee a clean slate.
    """
    for col in mock_collections.values():
        col.reset_mock()
        for attr in ("find_one", "find", "insert_one", "insert_many", "update_one", "delete_one", "count_documents"):
            method = getattr(col, attr, None)
            if method is not None:
                method.side_effect = None
                method.return_value = None
    with (
        patch("app.main.usrcollection", mock_collections["usr"]),
        patch("app.main.dccollection", mock_collections["dgr"]),
        patch("app.core.verificator.usrcollection", mock_collections["usr"]),
        patch("app.core.verificator.dccollection", mock_collections["dgr"]),
    ):
        from app.main import app
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            yield ac, mock_collections
