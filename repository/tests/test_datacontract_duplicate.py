"""
Tests for duplicate-prevention pada POST /datacontract/add.
Covers Issue #12 — backend cegah insert duplikat contract_number.
"""

import pytest


VALID_CONTRACT = {
    "standard_version": "1.0",
    "contract_number": "TESTDUP123",
    "metadata": {
        "version": "1.0.0",
        "type": "dataset",
        "name": "Test Kontrak",
        "owner": "tim_test",
    },
    "model": [],
    "ports": [],
    "examples": {"type": None, "data": None},
}


@pytest.fixture
def auth_bypass(client):
    """Override auth deps + reset dgr mock so call history doesn't bleed across tests."""
    from app.main import app
    from app.core.verificator import token_verification, access_verification

    _, mocks = client
    mocks["dgr"].reset_mock()

    async def fake_user():
        return {"usr": "tester", "lvl": "user", "sts": True}

    async def fake_access(*args, **kwargs):
        return None

    app.dependency_overrides[token_verification] = fake_user
    app.dependency_overrides[access_verification] = fake_access
    yield
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_add_contract_inserts_when_new(client, auth_bypass):
    ac, mocks = client
    mocks["dgr"].find_one.return_value = None
    mocks["dgr"].insert_one.return_value = None

    response = await ac.post("/datacontract/add", json=VALID_CONTRACT)
    assert response.status_code == 200
    mocks["dgr"].insert_one.assert_awaited_once()


@pytest.mark.asyncio
async def test_add_contract_returns_409_when_contract_number_exists(client, auth_bypass):
    ac, mocks = client
    mocks["dgr"].find_one.return_value = {"_id": "abc123"}

    response = await ac.post("/datacontract/add", json=VALID_CONTRACT)
    assert response.status_code == 409
    mocks["dgr"].insert_one.assert_not_called()


@pytest.mark.asyncio
async def test_add_contract_returns_409_on_duplicate_key_race(client, auth_bypass):
    """
    Race condition: find_one melaporkan kosong, tapi insert_one race-condition
    tertahan oleh unique index → DuplicateKeyError dari Mongo. Endpoint harus
    map ke 409, bukan crash.
    """
    from pymongo.errors import DuplicateKeyError

    ac, mocks = client
    mocks["dgr"].find_one.return_value = None
    mocks["dgr"].insert_one.side_effect = DuplicateKeyError("dup")

    response = await ac.post("/datacontract/add", json=VALID_CONTRACT)
    assert response.status_code == 409
