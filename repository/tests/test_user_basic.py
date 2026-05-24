"""
Tests untuk endpoint GET /user/basic — direktori user ringan
untuk dropdown stakeholder (ADR-0004 / Issue #27).

Kontrak:
- Bisa diakses oleh semua role (require_any).
- Hanya mengembalikan {username, name} dari user aktif (is_active=True)
  dan bukan service account (type != "sa").
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock


def _make_cursor(items):
    cursor = MagicMock()
    cursor.to_list = AsyncMock(return_value=items)
    return cursor


@pytest.fixture
def auth_bypass(client):
    from app.main import app
    from app.core.verificator import token_verification, access_verification

    async def fake_user():
        return {"usr": "anyone", "lvl": "user", "sts": True}
    async def fake_access(*args, **kwargs):
        return None

    app.dependency_overrides[token_verification] = fake_user
    app.dependency_overrides[access_verification] = fake_access
    yield
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_user_basic_returns_username_name_only(client, auth_bypass):
    ac, mocks = client
    items = [
        {"username": "retno",   "name": "Bu Retno"},
        {"username": "dimas",   "name": "Mas Dimas"},
        {"username": "indah",   "name": "Mbak Indah"},
    ]
    mocks["usr"].find = MagicMock(return_value=_make_cursor(items))

    resp = await ac.get("/user/basic")
    assert resp.status_code == 200
    assert resp.json() == items

    # Pastikan projection minimal — query memang hanya minta 2 field + _id excl.
    call = mocks["usr"].find.call_args
    projection = call.args[1] if len(call.args) > 1 else call.kwargs.get("projection")
    assert projection == {"_id": 0, "username": 1, "name": 1}


@pytest.mark.asyncio
async def test_user_basic_filters_inactive_and_service_accounts(client, auth_bypass):
    ac, mocks = client
    mocks["usr"].find = MagicMock(return_value=_make_cursor([]))

    await ac.get("/user/basic")

    # Filter yang dipakai harus mengecualikan user inaktif dan SA.
    filt = mocks["usr"].find.call_args.args[0]
    assert filt == {"is_active": True, "type": {"$ne": "sa"}}
