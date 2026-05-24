"""
Tests untuk auto-seed root account dari SEED_ROOT_* env vars (issue #32).

Sasaran perilaku:
- Env tidak di-set → tidak ada aksi (skip diam-diam).
- Env di-set, tidak ada root aktif → root baru dibuat.
- Env di-set, root aktif sudah ada → skip (idempotent).
- Password lemah → RuntimeError saat startup (fail-fast).
"""

import pytest
from unittest.mock import AsyncMock


@pytest.fixture(autouse=True)
def _reset_seed_env(monkeypatch):
    """Pastikan env SEED_ROOT_* bersih di tiap test — supaya tidak bocor
    dari shell maintainer atau test lain."""
    for var in ("SEED_ROOT_USERNAME", "SEED_ROOT_PASSWORD",
                "SEED_ROOT_NAME", "SEED_ROOT_DOMAIN"):
        monkeypatch.delenv(var, raising=False)


@pytest.mark.asyncio
async def test_seed_skipped_when_env_not_set(client):
    from app.main import _seed_root_from_env
    _, mocks = client
    mocks["usr"].find_one = AsyncMock()
    mocks["usr"].insert_one = AsyncMock()

    await _seed_root_from_env()

    mocks["usr"].find_one.assert_not_called()
    mocks["usr"].insert_one.assert_not_called()


@pytest.mark.asyncio
async def test_seed_creates_root_when_env_set_and_no_root(client, monkeypatch):
    from app.main import _seed_root_from_env
    _, mocks = client

    monkeypatch.setenv("SEED_ROOT_USERNAME", "rooty")
    monkeypatch.setenv("SEED_ROOT_PASSWORD", "Sandi!Aman123")
    monkeypatch.setenv("SEED_ROOT_NAME",     "Super Admin")
    monkeypatch.setenv("SEED_ROOT_DOMAIN",   "root")

    mocks["usr"].find_one = AsyncMock(return_value=None)
    mocks["usr"].update_many = AsyncMock()
    mocks["usr"].insert_one = AsyncMock()

    await _seed_root_from_env()

    mocks["usr"].insert_one.assert_awaited_once()
    doc = mocks["usr"].insert_one.await_args.args[0]
    assert doc["username"] == "rooty"
    assert doc["name"] == "Super Admin"
    assert doc["group_access"] == "root"
    assert doc["data_domain"] == "root"
    assert doc["is_active"] is True
    # password harus di-hash, bukan plaintext
    assert doc["password"] != "Sandi!Aman123"


@pytest.mark.asyncio
async def test_seed_idempotent_when_root_exists(client, monkeypatch):
    from app.main import _seed_root_from_env
    _, mocks = client

    monkeypatch.setenv("SEED_ROOT_USERNAME", "rooty")
    monkeypatch.setenv("SEED_ROOT_PASSWORD", "Sandi!Aman123")

    mocks["usr"].find_one = AsyncMock(return_value={"username": "existing-root", "is_active": True})
    mocks["usr"].insert_one = AsyncMock()

    await _seed_root_from_env()

    # Tidak insert — root aktif sudah ada.
    mocks["usr"].insert_one.assert_not_called()


@pytest.mark.asyncio
async def test_seed_raises_on_weak_password(client, monkeypatch):
    from app.main import _seed_root_from_env
    _, mocks = client

    monkeypatch.setenv("SEED_ROOT_USERNAME", "rooty")
    monkeypatch.setenv("SEED_ROOT_PASSWORD", "weak")  # too short, no upper/digit/special

    mocks["usr"].find_one = AsyncMock()
    mocks["usr"].insert_one = AsyncMock()

    with pytest.raises(RuntimeError, match="SEED_ROOT_PASSWORD invalid"):
        await _seed_root_from_env()

    # find_one tidak boleh terpanggil — validation gagal lebih dulu.
    mocks["usr"].find_one.assert_not_called()


@pytest.mark.asyncio
async def test_seed_skipped_when_only_username_set(client, monkeypatch):
    """Kalau hanya satu dari pair username/password di-set, treat as "not configured"."""
    from app.main import _seed_root_from_env
    _, mocks = client

    monkeypatch.setenv("SEED_ROOT_USERNAME", "rooty")
    # tidak set password

    mocks["usr"].find_one = AsyncMock()
    mocks["usr"].insert_one = AsyncMock()

    await _seed_root_from_env()

    mocks["usr"].find_one.assert_not_called()
    mocks["usr"].insert_one.assert_not_called()
