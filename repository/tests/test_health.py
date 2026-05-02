import pytest


@pytest.mark.asyncio
async def test_health_returns_ok(client):
    ac, _ = client
    response = await ac.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "version" in body
