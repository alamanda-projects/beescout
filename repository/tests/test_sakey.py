"""
Tests for SA Key creation role gating.
Regression for issue #31 — role `user` must NOT be able to create SA keys,
only `developer`, `admin`, and `root`.
"""

import pytest
from unittest.mock import AsyncMock, patch


def _payload(level: str) -> dict:
    return {
        "usr": f"someone_{level}",
        "typ": "user",
        "lvl": level,
        "sts": True,
        "tim": "platform",
    }


@pytest.fixture
def override_token(monkeypatch):
    from app.main import app
    from app.core.verificator import token_verification

    def _set(level: str):
        app.dependency_overrides[token_verification] = lambda: _payload(level)

    yield _set
    app.dependency_overrides.pop(token_verification, None)


@pytest.mark.asyncio
@pytest.mark.parametrize("level", ["developer", "admin", "root"])
async def test_sakey_create_allowed_for_privileged_roles(client, override_token, level):
    ac, mocks = client
    mocks["usr"].find_one.return_value = {"username": _payload(level)["usr"], "is_active": True}
    mocks["usr"].insert_one.return_value = None
    override_token(level)
    response = await ac.get("/sakey/create")
    assert response.status_code == 200, response.text
    assert "client_id" in response.json()


@pytest.mark.asyncio
async def test_sakey_create_forbidden_for_user_role(client, override_token):
    ac, mocks = client
    mocks["usr"].find_one.return_value = {"username": "biz_user", "is_active": True}
    mocks["usr"].insert_one.reset_mock()
    override_token("user")
    response = await ac.get("/sakey/create")
    assert response.status_code == 403
    mocks["usr"].insert_one.assert_not_called()
