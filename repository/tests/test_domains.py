"""
Tests for domain management endpoints (issue #34).

Covers: CRUD on /domain/*, slugify behaviour, soft delete, role gating,
and the data_domain validation wired into /user/create.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock


def _payload(level: str) -> dict:
    return {
        "usr": f"someone_{level}",
        "typ": "user",
        "lvl": level,
        "sts": True,
        "tim": "platform",
    }


@pytest.fixture
def override_token():
    from app.main import app
    from app.core.verificator import token_verification

    def _set(level: str):
        app.dependency_overrides[token_verification] = lambda: _payload(level)

    yield _set
    app.dependency_overrides.pop(token_verification, None)


def _cursor(docs):
    """A sync find() result whose to_list() is awaitable."""
    cur = MagicMock()
    cur.to_list = AsyncMock(return_value=docs)
    return cur


# ── Create ────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_domain_success(client, override_token):
    ac, mocks = client
    mocks["dom"].find_one.return_value = None
    mocks["dom"].insert_one.return_value = None
    override_token("admin")
    res = await ac.post("/domain/create", json={"name": "Penjualan", "label": "Penjualan"})
    assert res.status_code == 201, res.text
    # name di-slugify jadi lowercase
    assert res.json()["name"] == "penjualan"


@pytest.mark.asyncio
async def test_create_domain_slugifies_spaces(client, override_token):
    ac, mocks = client
    mocks["dom"].find_one.return_value = None
    mocks["dom"].insert_one.return_value = None
    override_token("admin")
    res = await ac.post("/domain/create", json={"name": "  Tim  Gudang ", "label": "Tim Gudang"})
    assert res.status_code == 201, res.text
    assert res.json()["name"] == "tim-gudang"


@pytest.mark.asyncio
async def test_create_domain_duplicate_rejected(client, override_token):
    ac, mocks = client
    mocks["dom"].find_one.return_value = {"name": "penjualan", "label": "Penjualan"}
    override_token("admin")
    res = await ac.post("/domain/create", json={"name": "penjualan", "label": "Penjualan"})
    assert res.status_code == 409


@pytest.mark.asyncio
async def test_create_domain_requires_label(client, override_token):
    ac, mocks = client
    mocks["dom"].find_one.return_value = None
    override_token("admin")
    res = await ac.post("/domain/create", json={"name": "penjualan", "label": "   "})
    assert res.status_code == 412


@pytest.mark.asyncio
async def test_create_domain_forbidden_for_non_admin(client, override_token):
    ac, _ = client
    override_token("user")
    res = await ac.post("/domain/create", json={"name": "penjualan", "label": "Penjualan"})
    assert res.status_code == 403


# ── List ──────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_domains_returns_active(client, override_token):
    ac, mocks = client
    mocks["dom"].find = MagicMock(return_value=_cursor([
        {"name": "penjualan", "label": "Penjualan", "is_active": True},
    ]))
    mocks["usr"].count_documents.return_value = 3
    override_token("admin")
    res = await ac.get("/domain/lists")
    assert res.status_code == 200, res.text
    body = res.json()
    assert body[0]["name"] == "penjualan"
    assert body[0]["user_count"] == 3


# ── Update ────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_update_domain_label(client, override_token):
    ac, mocks = client
    mocks["dom"].find_one.return_value = {"name": "penjualan", "label": "Penjualan"}
    mocks["dom"].update_one.return_value = None
    override_token("admin")
    res = await ac.patch("/domain/penjualan", json={"label": "Penjualan B2B"})
    assert res.status_code == 200, res.text


@pytest.mark.asyncio
async def test_update_domain_not_found(client, override_token):
    ac, mocks = client
    mocks["dom"].find_one.return_value = None
    override_token("admin")
    res = await ac.patch("/domain/ghost", json={"label": "Ghost"})
    assert res.status_code == 404


# ── Deactivate (soft delete) ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_deactivate_domain_soft_deletes(client, override_token):
    ac, mocks = client
    mocks["dom"].find_one.return_value = {"name": "penjualan", "is_active": True}
    mocks["dom"].update_one.return_value = None
    override_token("admin")
    res = await ac.delete("/domain/penjualan")
    assert res.status_code == 200, res.text
    # soft delete → update_one set is_active False, bukan delete_one
    mocks["dom"].update_one.assert_awaited_once()
    args = mocks["dom"].update_one.await_args
    assert args[0][1] == {"$set": {"is_active": False}}
    mocks["dom"].delete_one.assert_not_called()


@pytest.mark.asyncio
async def test_deactivate_domain_not_found(client, override_token):
    ac, mocks = client
    mocks["dom"].find_one.return_value = None
    override_token("admin")
    res = await ac.delete("/domain/ghost")
    assert res.status_code == 404


# ── data_domain validation on /user/create ────────────────────────────────────

VALID_USER = {
    "username": "dimas",
    "name": "Mas Dimas",
    "password": "Str0ng!Pass",
    "group_access": "user",
    "data_domain": "penjualan",
    "is_active": True,
}


@pytest.mark.asyncio
async def test_user_create_rejects_unknown_domain(client, override_token):
    ac, mocks = client
    mocks["usr"].find_one.return_value = None
    # katalog domain sudah dipakai → validasi aktif
    mocks["dom"].count_documents.return_value = 2
    mocks["dom"].find_one.return_value = None  # domain tidak ditemukan
    override_token("root")
    res = await ac.post("/user/create", json=VALID_USER)
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_user_create_accepts_registered_domain(client, override_token):
    ac, mocks = client
    mocks["usr"].find_one.return_value = None
    mocks["usr"].insert_one.return_value = None
    mocks["dom"].count_documents.return_value = 2
    mocks["dom"].find_one.return_value = {"name": "penjualan", "is_active": True}
    override_token("root")
    res = await ac.post("/user/create", json=VALID_USER)
    assert res.status_code == 200, res.text


@pytest.mark.asyncio
async def test_user_create_skips_validation_when_catalog_empty(client, override_token):
    ac, mocks = client
    mocks["usr"].find_one.return_value = None
    mocks["usr"].insert_one.return_value = None
    # katalog domain kosong → validasi dilewati (backward compatible)
    mocks["dom"].count_documents.return_value = 0
    override_token("root")
    res = await ac.post("/user/create", json=VALID_USER)
    assert res.status_code == 200, res.text
