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
        "effective_date": "2024-01-01",
        "expiry_date": "2025-12-31",
        # #102 PR-B: description wajib di write-path.
        "description": {"purpose": "Analisis penjualan", "usage": "private"},
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
async def test_add_contract_returns_422_when_description_missing(client, auth_bypass):
    """#102 PR-B: write-time enforcement — metadata.description.purpose & usage
    wajib. Tanpa keduanya → 422, insert tidak dipanggil."""
    ac, mocks = client
    mocks["dgr"].find_one.return_value = None

    payload = {**VALID_CONTRACT, "metadata": {**VALID_CONTRACT["metadata"]}}
    payload["metadata"].pop("description", None)

    response = await ac.post("/datacontract/add", json=payload)
    assert response.status_code == 422, response.text
    mocks["dgr"].insert_one.assert_not_called()


@pytest.mark.asyncio
async def test_add_contract_returns_422_when_usage_blank(client, auth_bypass):
    """purpose ada tapi usage kosong → tetap 422 (kedua field wajib)."""
    ac, mocks = client
    mocks["dgr"].find_one.return_value = None

    payload = {**VALID_CONTRACT, "metadata": {**VALID_CONTRACT["metadata"],
               "description": {"purpose": "ada", "usage": "   "}}}

    response = await ac.post("/datacontract/add", json=payload)
    assert response.status_code == 422, response.text
    mocks["dgr"].insert_one.assert_not_called()


@pytest.mark.asyncio
async def test_add_contract_returns_422_when_stakeholder_email_missing(client, auth_bypass):
    """#102 PR-B slice 2: stakeholder ber-name tanpa email → 422."""
    ac, mocks = client
    mocks["dgr"].find_one.return_value = None

    payload = {**VALID_CONTRACT, "metadata": {**VALID_CONTRACT["metadata"],
               "stakeholders": [{"name": "Pak X", "role": "owner",
                                 "date_in": "2024-01-01"}]}}

    response = await ac.post("/datacontract/add", json=payload)
    assert response.status_code == 422, response.text
    assert "email" in response.text.lower()
    mocks["dgr"].insert_one.assert_not_called()


@pytest.mark.asyncio
async def test_add_contract_ok_when_stakeholder_has_email(client, auth_bypass):
    """Stakeholder lengkap (name + email + date_in) → lolos write-check."""
    ac, mocks = client
    mocks["dgr"].find_one.return_value = None
    mocks["dgr"].insert_one.return_value = None

    payload = {**VALID_CONTRACT, "metadata": {**VALID_CONTRACT["metadata"],
               "stakeholders": [{"name": "Pak X", "role": "owner",
                                 "email": "x@beescout.id", "date_in": "2024-01-01"}]}}

    response = await ac.post("/datacontract/add", json=payload)
    assert response.status_code == 200, response.text
    mocks["dgr"].insert_one.assert_awaited_once()


@pytest.mark.asyncio
async def test_add_contract_returns_422_when_model_type_missing(client, auth_bypass):
    """#102 PR-B slice 3: kolom ber-name tanpa logical_type/physical_type → 422."""
    ac, mocks = client
    mocks["dgr"].find_one.return_value = None

    payload = {**VALID_CONTRACT,
               "model": [{"column": "id", "logical_type": "UUID"}]}  # physical_type hilang

    response = await ac.post("/datacontract/add", json=payload)
    assert response.status_code == 422, response.text
    assert "physical_type" in response.text or "logical_type" in response.text
    mocks["dgr"].insert_one.assert_not_called()


@pytest.mark.asyncio
async def test_add_contract_returns_422_when_model_description_missing(client, auth_bypass):
    """#102 PR-B slice 4: kolom ber-name dengan tipe lengkap tapi tanpa
    description → 422."""
    ac, mocks = client
    mocks["dgr"].find_one.return_value = None

    payload = {**VALID_CONTRACT,
               "model": [{"column": "id", "logical_type": "UUID",
                          "physical_type": "VARCHAR(36)"}]}  # description hilang

    response = await ac.post("/datacontract/add", json=payload)
    assert response.status_code == 422, response.text
    assert "description" in response.text
    mocks["dgr"].insert_one.assert_not_called()


@pytest.mark.asyncio
async def test_add_contract_ok_when_model_complete(client, auth_bypass):
    """Kolom lengkap (logical + physical + description) → lolos write-check."""
    ac, mocks = client
    mocks["dgr"].find_one.return_value = None
    mocks["dgr"].insert_one.return_value = None

    payload = {**VALID_CONTRACT,
               "model": [{"column": "id", "logical_type": "UUID",
                          "physical_type": "VARCHAR(36)",
                          "description": "Identitas unik baris"}]}

    response = await ac.post("/datacontract/add", json=payload)
    assert response.status_code == 200, response.text
    mocks["dgr"].insert_one.assert_awaited_once()


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
