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
    "group_access": "root",
    "data_domain": "platform",
    "is_active": True,
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
