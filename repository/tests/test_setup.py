"""
Tests for the /setup bootstrap endpoint.
Covers: first-run success, duplicate prevention, password validation,
plus optional add-on imports (sample contracts & catalog rules).
"""

import pytest
from unittest.mock import AsyncMock, patch


VALID_PAYLOAD = {
    "username": "rootuser",
    "name": "Root User",
    "password": "Str0ng!Pass",
}


@pytest.mark.asyncio
async def test_setup_status_not_complete_initially(client):
    ac, mocks = client
    mocks["usr"].find_one.return_value = None
    response = await ac.get("/setup/status")
    assert response.status_code == 200
    assert response.json()["setup_complete"] is False


@pytest.mark.asyncio
async def test_setup_creates_root_when_none_exists(client):
    ac, mocks = client
    mocks["usr"].find_one.return_value = None
    mocks["usr"].insert_one.return_value = None
    response = await ac.post("/setup", json=VALID_PAYLOAD)
    assert response.status_code == 200
    assert "Root account created" in response.json()["message"]


@pytest.mark.asyncio
async def test_setup_returns_409_when_root_exists(client):
    ac, mocks = client
    mocks["usr"].find_one.return_value = {"username": "existing_root", "group_access": "root"}
    response = await ac.post("/setup", json=VALID_PAYLOAD)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_setup_disables_stale_root_before_creating_new(client):
    """Saat /setup berjalan (tidak ada root aktif), semua dokumen root lama
    di-disable lebih dulu agar hanya ada satu root aktif."""
    ac, mocks = client
    mocks["usr"].find_one.return_value = None  # tidak ada root aktif
    mocks["usr"].update_many.reset_mock()
    mocks["usr"].insert_one.return_value = None

    response = await ac.post("/setup", json=VALID_PAYLOAD)
    assert response.status_code == 200

    # root lama yang menggantung di-non-aktifkan sebelum root baru dibuat
    mocks["usr"].update_many.assert_called_once()
    query, update = mocks["usr"].update_many.call_args.args
    assert query == {"group_access": "root"}
    assert update == {"$set": {"is_active": False}}

    # root baru tetap dibuat sebagai aktif
    inserted = mocks["usr"].insert_one.call_args.args[0]
    assert inserted["group_access"] == "root"
    assert inserted["is_active"] is True


@pytest.mark.asyncio
async def test_setup_rejects_weak_password(client):
    ac, mocks = client
    mocks["usr"].find_one.return_value = None
    payload = {**VALID_PAYLOAD, "password": "weakpass"}
    response = await ac.post("/setup", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_setup_status_complete_when_root_exists(client):
    ac, mocks = client
    mocks["usr"].find_one.return_value = {"username": "root", "group_access": "root", "is_active": True}
    response = await ac.get("/setup/status")
    assert response.status_code == 200
    assert response.json()["setup_complete"] is True


# ── Add-on imports ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_setup_without_addons_does_not_seed(client):
    ac, mocks = client
    mocks["usr"].find_one.return_value = None
    mocks["dgr"].insert_one.reset_mock()
    response = await ac.post("/setup", json=VALID_PAYLOAD)
    assert response.status_code == 200
    body = response.json()
    assert body["sample_contracts_imported"] is False
    assert body["catalog_rules_imported"] is False
    mocks["dgr"].insert_one.assert_not_called()


@pytest.mark.asyncio
async def test_setup_imports_sample_contracts_when_flag_set(client):
    ac, mocks = client
    mocks["usr"].find_one.return_value = None
    mocks["dgr"].insert_one.reset_mock()
    mocks["dgr"].insert_one.return_value = None
    payload = {**VALID_PAYLOAD, "import_sample_contracts": True}
    response = await ac.post("/setup", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["sample_contracts_imported"] is True
    assert body["sample_contracts_count"] >= 1
    mocks["dgr"].insert_one.assert_called()
    # created_by should be overridden to the new root user
    inserted = mocks["dgr"].insert_one.call_args.args[0]
    assert inserted["created_by"] == VALID_PAYLOAD["username"]


@pytest.mark.asyncio
async def test_setup_imports_catalog_rules_when_flag_set(client):
    ac, mocks = client
    mocks["usr"].find_one.return_value = None
    catalog_mock = AsyncMock()
    catalog_mock.count_documents.return_value = 0
    catalog_mock.insert_many.return_value = None
    with patch("app.main.catalogcollection", catalog_mock):
        payload = {**VALID_PAYLOAD, "import_catalog_rules": True}
        response = await ac.post("/setup", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["catalog_rules_imported"] is True
    assert body["catalog_rules_count"] > 0
    catalog_mock.insert_many.assert_called_once()


@pytest.mark.asyncio
async def test_setup_skips_catalog_rules_if_already_seeded(client):
    ac, mocks = client
    mocks["usr"].find_one.return_value = None
    catalog_mock = AsyncMock()
    catalog_mock.count_documents.return_value = 5  # sudah ada
    with patch("app.main.catalogcollection", catalog_mock):
        payload = {**VALID_PAYLOAD, "import_catalog_rules": True}
        response = await ac.post("/setup", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["catalog_rules_imported"] is False
    catalog_mock.insert_many.assert_not_called()


# ── Default domain seed (#74) ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_setup_seeds_default_domains_when_empty(client):
    """Fresh /setup → katalog `domains` harus berisi 'root' & 'admin'."""
    ac, mocks = client
    mocks["usr"].find_one.return_value = None
    mocks["dom"].find_one.return_value = None  # belum ada domain apa pun

    response = await ac.post("/setup", json=VALID_PAYLOAD)
    assert response.status_code == 200

    insert_calls = mocks["dom"].insert_one.call_args_list
    inserted_names = [call.args[0]["name"] for call in insert_calls]
    assert set(inserted_names) == {"root", "admin"}
    for call in insert_calls:
        doc = call.args[0]
        assert doc["is_default"] is True
        assert doc["is_active"] is True


@pytest.mark.asyncio
async def test_setup_hardsets_root_data_domain_to_root(client):
    """SetupRequest tidak punya data_domain (#84) — kalau client iseng kirim
    field ekstra, Pydantic mengabaikannya dan root tetap di domain 'root'."""
    ac, mocks = client
    mocks["usr"].find_one.return_value = None
    payload = {**VALID_PAYLOAD, "data_domain": "marketing"}  # field iseng

    response = await ac.post("/setup", json=payload)
    assert response.status_code == 200

    inserted = mocks["usr"].insert_one.call_args.args[0]
    assert inserted["data_domain"] == "root"


@pytest.mark.asyncio
async def test_setup_does_not_duplicate_default_domains(client):
    """Idempoten: kalau domain default sudah ada, /setup tidak meng-insert lagi."""
    ac, mocks = client
    mocks["usr"].find_one.return_value = None
    # Anggap kedua domain default sudah ada di katalog.
    mocks["dom"].find_one.return_value = {"name": "root", "is_default": True}

    response = await ac.post("/setup", json=VALID_PAYLOAD)
    assert response.status_code == 200

    mocks["dom"].insert_one.assert_not_called()


