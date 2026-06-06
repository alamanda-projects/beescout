"""
Tests untuk write-time enforcement: minimal 1 stakeholder dengan role
consumer/producer wajib di metadata.stakeholders (ADR-0007).

Pydantic Metadata.stakeholders tetap Optional supaya read path lenient
untuk kontrak legacy. Enforcement terjadi di 3 lapis:
- FE zod (form wizard) — tidak di-cover di test ini
- Write-time check di handler POST /datacontract/add & PUT /update
- POST /contracts/import-yaml (bypass Pydantic, cek manual via dict)

Tanpa stakeholder visibility-giving, kontrak yatim — tidak terlihat oleh
siapa pun selain admin (lihat derive_team_scope di verificator.py).
"""

import io
import pytest


def _base_contract(stakeholders=None):
    """Payload kontrak minimal valid. Stakeholders bisa di-override."""
    return {
        "standard_version": "1.0",
        "contract_number": "TEST_SH_001",
        "metadata": {
            "version": "1.0.0",
            "type": "dataset",
            "name": "Kontrak Test",
            "owner": "tim_test",
            "effective_date": "2024-01-01",
            "expiry_date": "2025-12-31",
            # #102 PR-B: description wajib di write-path.
            "description": {"purpose": "Test purpose", "usage": "private"},
            "stakeholders": stakeholders if stakeholders is not None else [],
        },
        "model": [],
        "ports": [],
        "examples": {"type": None, "data": None},
    }


@pytest.fixture
def auth_bypass(client):
    """Override auth deps + reset dgr mock biar history tidak bleed antar test."""
    from app.main import app
    from app.core.verificator import token_verification, access_verification

    _, mocks = client
    mocks["dgr"].reset_mock()

    async def fake_user():
        return {"usr": "tester", "lvl": "admin", "sts": True, "tim": "tim_test"}

    async def fake_access(*args, **kwargs):
        return None

    app.dependency_overrides[token_verification] = fake_user
    app.dependency_overrides[access_verification] = fake_access
    yield
    app.dependency_overrides.clear()


# ── POST /datacontract/add ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_add_rejects_empty_stakeholders(client, auth_bypass):
    """Stakeholders kosong → 422, insert tidak dipanggil."""
    ac, mocks = client
    mocks["dgr"].find_one.return_value = None

    res = await ac.post("/datacontract/add", json=_base_contract(stakeholders=[]))
    assert res.status_code == 422
    assert "consumer" in res.json()["detail"] and "producer" in res.json()["detail"]
    mocks["dgr"].insert_one.assert_not_called()


@pytest.mark.asyncio
async def test_add_rejects_owner_only(client, auth_bypass):
    """Hanya stakeholder owner (tanpa consumer/producer) → 422."""
    ac, mocks = client
    mocks["dgr"].find_one.return_value = None

    payload = _base_contract(stakeholders=[{"name": "Pak X", "role": "owner", "email": "pak.x@example.com", "date_in": "2024-01-01"}])
    res = await ac.post("/datacontract/add", json=payload)
    assert res.status_code == 422
    mocks["dgr"].insert_one.assert_not_called()


@pytest.mark.asyncio
async def test_add_rejects_reviewer_only(client, auth_bypass):
    """Hanya reviewer → 422. Reviewer tidak memberi team-scope visibility."""
    ac, mocks = client
    mocks["dgr"].find_one.return_value = None

    payload = _base_contract(stakeholders=[{"name": "Bu R", "role": "reviewer", "email": "bu.r@example.com", "date_in": "2024-01-01"}])
    res = await ac.post("/datacontract/add", json=payload)
    assert res.status_code == 422
    mocks["dgr"].insert_one.assert_not_called()


@pytest.mark.asyncio
async def test_add_accepts_consumer_stakeholder(client, auth_bypass):
    """Minimal 1 consumer → 200, insert dipanggil."""
    ac, mocks = client
    mocks["dgr"].find_one.return_value = None

    payload = _base_contract(stakeholders=[{"name": "Tim Sales", "role": "consumer", "email": "tim.sales@example.com", "date_in": "2024-01-01"}])
    res = await ac.post("/datacontract/add", json=payload)
    assert res.status_code == 200, res.text
    mocks["dgr"].insert_one.assert_awaited_once()


@pytest.mark.asyncio
async def test_add_accepts_producer_stakeholder(client, auth_bypass):
    """Minimal 1 producer → 200. Producer simetri (ADR-0007)."""
    ac, mocks = client
    mocks["dgr"].find_one.return_value = None

    payload = _base_contract(stakeholders=[{"name": "Tim Eng", "role": "producer", "email": "tim.eng@example.com", "date_in": "2024-01-01"}])
    res = await ac.post("/datacontract/add", json=payload)
    assert res.status_code == 200, res.text
    mocks["dgr"].insert_one.assert_awaited_once()


@pytest.mark.asyncio
async def test_add_accepts_mixed_with_consumer(client, auth_bypass):
    """Campuran role tapi minimal ada 1 consumer/producer → 200."""
    ac, mocks = client
    mocks["dgr"].find_one.return_value = None

    payload = _base_contract(stakeholders=[
        {"name": "Pak X", "role": "owner", "email": "pak.x@example.com", "date_in": "2024-01-01"},
        {"name": "Bu R", "role": "reviewer", "email": "bu.r@example.com", "date_in": "2024-01-01"},
        {"name": "Tim Sales", "role": "consumer", "email": "tim.sales@example.com", "date_in": "2024-01-01"},
    ])
    res = await ac.post("/datacontract/add", json=payload)
    assert res.status_code == 200, res.text
    mocks["dgr"].insert_one.assert_awaited_once()


# ── PUT /datacontract/update ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_update_rejects_stripped_stakeholders(client, auth_bypass):
    """Edit kontrak: payload menghilangkan stakeholder consumer/producer → 422.
    Mencegah workaround 'create lalu hapus stakeholder via edit'."""
    ac, mocks = client
    # Kontrak existing punya consumer; payload baru hanya owner.
    mocks["dgr"].find_one.return_value = {
        "_id": "x", "contract_number": "TEST_SH_001",
        "created_by": "tester", "managers": [],
        "metadata": {"stakeholders": [{"name": "Tim Sales", "role": "consumer"}]},
    }

    payload = _base_contract(stakeholders=[{"name": "Pak X", "role": "owner", "email": "pak.x@example.com", "date_in": "2024-01-01"}])
    payload["contract_number"] = "TEST_SH_001"
    res = await ac.put(
        "/datacontract/update",
        params={"contract_number": "TEST_SH_001"},
        json=payload,
    )
    assert res.status_code == 422
    mocks["dgr"].update_one.assert_not_called()


@pytest.mark.asyncio
async def test_update_accepts_when_consumer_kept(client, auth_bypass):
    """Edit dengan consumer dipertahankan → sukses. Admin → langsung apply."""
    ac, mocks = client
    mocks["dgr"].find_one.return_value = {
        "_id": "x", "contract_number": "TEST_SH_001",
        "created_by": "tester", "managers": [],
        "metadata": {"stakeholders": [{"name": "Tim Sales", "role": "consumer"}]},
    }

    payload = _base_contract(stakeholders=[{"name": "Tim Sales 2", "role": "consumer", "email": "tim.sales2@example.com", "date_in": "2024-01-01"}])
    payload["contract_number"] = "TEST_SH_001"
    res = await ac.put(
        "/datacontract/update",
        params={"contract_number": "TEST_SH_001"},
        json=payload,
    )
    assert res.status_code == 200, res.text
    mocks["dgr"].update_one.assert_awaited()


# ── POST /contracts/import-yaml ──────────────────────────────────────────────


@pytest.fixture
def admin_bypass(client):
    """Override require_admin untuk YAML import endpoint."""
    from app.main import app, require_admin

    _, mocks = client
    mocks["dgr"].reset_mock()

    async def fake_admin():
        return {"usr": "admin", "lvl": "admin", "sts": True}

    app.dependency_overrides[require_admin] = fake_admin
    yield
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_import_yaml_rejects_no_visibility_stakeholder(client, admin_bypass):
    """YAML import tanpa stakeholder consumer/producer → 422."""
    ac, mocks = client
    yaml_content = """\
standard_version: '1.0'
contract_number: YAML_TEST_001
metadata:
  version: '1.0.0'
  type: dataset
  name: Test YAML
  owner: tim_test
  effective_date: '2024-01-01'
  expiry_date: '2025-12-31'
  stakeholders:
    - name: Pak X
      role: owner
model: []
ports: []
"""
    res = await ac.post(
        "/contracts/import-yaml",
        files={"file": ("test.yaml", io.BytesIO(yaml_content.encode()), "text/yaml")},
    )
    assert res.status_code == 422
    mocks["dgr"].insert_one.assert_not_called()


@pytest.mark.asyncio
async def test_import_yaml_accepts_consumer_stakeholder(client, admin_bypass):
    """YAML import dengan consumer stakeholder → 201."""
    ac, mocks = client
    mocks["dgr"].find_one.return_value = None
    yaml_content = """\
standard_version: '1.0'
contract_number: YAML_TEST_002
metadata:
  version: '1.0.0'
  type: dataset
  name: Test YAML OK
  owner: tim_test
  effective_date: '2024-01-01'
  expiry_date: '2025-12-31'
  description:
    purpose: Untuk analisis penjualan
    usage: private
  stakeholders:
    - name: Tim Sales
      role: consumer
      email: tim.sales@example.com
      date_in: '2024-01-01'
model: []
ports: []
"""

    # find_one dipanggil 2x: cek existing & ambil saved. Pakai side_effect
    # supaya call kedua return dokumen ter-insert.
    saved_doc = {
        "contract_number": "YAML_TEST_002",
        "metadata": {"name": "Test YAML OK"},
    }
    mocks["dgr"].find_one.side_effect = [None, saved_doc]

    res = await ac.post(
        "/contracts/import-yaml",
        files={"file": ("test.yaml", io.BytesIO(yaml_content.encode()), "text/yaml")},
    )
    assert res.status_code == 201, res.text
    mocks["dgr"].insert_one.assert_awaited_once()
