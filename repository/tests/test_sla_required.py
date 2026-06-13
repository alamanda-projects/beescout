"""Tests untuk write-time enforcement SLA spec-YES fields (#102 PR-B slice 5).

Verifikasi bahwa /datacontract/add, /datacontract/update,
/contracts/validate-yaml, dan /contracts/import-yaml menolak
kontrak tanpa SLA spec fields yang lengkap:
  - metadata.sla.availability_start (int)
  - metadata.sla.availability_end (int)
  - metadata.sla.availability_unit (str: 'h' | 'd')
  - metadata.sla.frequency (int)
  - metadata.sla.frequency_unit (str: 'm' | 'h' | 'd')
"""

import io
import pytest


def _base_contract(sla=None):
    """Payload kontrak minimal valid. SLA bisa di-override."""
    base_sla = {
        "availability_start": 6,
        "availability_end": 18,
        "availability_unit": "h",
        "frequency": 4,
        "frequency_unit": "h",
    }
    return {
        "standard_version": "1.0",
        "contract_number": "TEST_SLA_001",
        "metadata": {
            "version": "1.0.0",
            "type": "dataset",
            "name": "Kontrak Test SLA",
            "owner": "tim_test",
            "effective_date": "2024-01-01",
            "expiry_date": "2025-12-31",
            "description": {"purpose": "Test SLA", "usage": "private"},
            "stakeholders": [{"name": "Tim Sales", "role": "consumer",
                               "email": "sales@test.com", "date_in": "2024-01-01"}],
            "sla": sla if sla is not None else base_sla,
        },
        "model": [],
        "ports": [],
        "examples": {"type": None, "data": None},
    }


@pytest.fixture
def auth_bypass(client):
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


@pytest.fixture
def admin_bypass(client):
    from app.main import app, require_admin

    _, mocks = client
    mocks["dgr"].reset_mock()

    async def fake_admin():
        return {"usr": "admin", "lvl": "admin", "sts": True}

    app.dependency_overrides[require_admin] = fake_admin
    yield
    app.dependency_overrides.clear()


# ── POST /datacontract/add ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_add_accepts_complete_sla(client, auth_bypass):
    """SLA lengkap → 200, insert dipanggil."""
    ac, mocks = client
    mocks["dgr"].find_one.return_value = None

    res = await ac.post("/datacontract/add", json=_base_contract())
    assert res.status_code == 200, res.text
    mocks["dgr"].insert_one.assert_awaited_once()


@pytest.mark.asyncio
async def test_add_rejects_missing_sla_block(client, auth_bypass):
    """Tidak ada sla block sama sekali → 422."""
    ac, mocks = client
    mocks["dgr"].find_one.return_value = None

    payload = _base_contract(sla=None)
    payload["metadata"].pop("sla", None)
    res = await ac.post("/datacontract/add", json=payload)
    assert res.status_code == 422, res.text
    assert "sla" in res.json()["detail"].lower() or "availability_start" in res.json()["detail"]
    mocks["dgr"].insert_one.assert_not_called()


@pytest.mark.asyncio
async def test_add_rejects_missing_availability_start(client, auth_bypass):
    """availability_start kosong → 422."""
    ac, mocks = client
    mocks["dgr"].find_one.return_value = None

    sla = {"availability_end": 18, "availability_unit": "h", "frequency": 4, "frequency_unit": "h"}
    res = await ac.post("/datacontract/add", json=_base_contract(sla=sla))
    assert res.status_code == 422, res.text
    assert "availability_start" in res.json()["detail"]
    mocks["dgr"].insert_one.assert_not_called()


@pytest.mark.asyncio
async def test_add_rejects_missing_frequency_unit(client, auth_bypass):
    """frequency_unit kosong → 422."""
    ac, mocks = client
    mocks["dgr"].find_one.return_value = None

    sla = {"availability_start": 6, "availability_end": 18, "availability_unit": "h", "frequency": 4}
    res = await ac.post("/datacontract/add", json=_base_contract(sla=sla))
    assert res.status_code == 422, res.text
    assert "frequency_unit" in res.json()["detail"]
    mocks["dgr"].insert_one.assert_not_called()


@pytest.mark.asyncio
async def test_add_accepts_frequency_zero(client, auth_bypass):
    """frequency: 0 (streaming) → tetap 200 (0 adalah nilai valid spec)."""
    ac, mocks = client
    mocks["dgr"].find_one.return_value = None

    sla = {"availability_start": 0, "availability_end": 23, "availability_unit": "h",
           "frequency": 0, "frequency_unit": "h"}
    res = await ac.post("/datacontract/add", json=_base_contract(sla=sla))
    assert res.status_code == 200, res.text
    mocks["dgr"].insert_one.assert_awaited_once()


# ── PUT /datacontract/update ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_update_rejects_missing_sla_fields(client, auth_bypass):
    """Update tanpa SLA spec fields → 422."""
    ac, mocks = client
    mocks["dgr"].find_one.return_value = {
        "_id": "x", "contract_number": "TEST_SLA_001",
        "created_by": "tester", "managers": [],
        "metadata": {"stakeholders": [{"name": "Tim Sales", "role": "consumer"}]},
    }

    payload = _base_contract(sla={"availability_end": 18})
    payload["contract_number"] = "TEST_SLA_001"
    res = await ac.put("/datacontract/update", params={"contract_number": "TEST_SLA_001"}, json=payload)
    assert res.status_code == 422, res.text
    mocks["dgr"].update_one.assert_not_called()


# ── POST /contracts/validate-yaml ─────────────────────────────────────────────

def _minimal_yaml_sla(sla: dict | None = None) -> bytes:
    import yaml as _yaml
    sla_block = sla if sla is not None else {
        "availability_start": 6, "availability_end": 18,
        "availability_unit": "h", "frequency": 4, "frequency_unit": "h",
    }
    doc = {
        "standard_version": "1.0.0",
        "contract_number": "CN-SLA-TEST",
        "metadata": {
            "name": "Test SLA", "owner": "Tim Test",
            "version": "1.0.0", "type": "CSV",
            "effective_date": "2024-01-01", "expiry_date": "2025-12-31",
            "description": {"purpose": "Test", "usage": "private"},
            "sla": sla_block,
            "stakeholders": [{"name": "Tim Sales", "role": "consumer",
                               "email": "sales@test.com", "date_in": "2024-01-01"}],
        },
        "model": [],
        "ports": [],
    }
    return _yaml.dump(doc, allow_unicode=True).encode("utf-8")


@pytest.mark.asyncio
async def test_validate_accepts_complete_sla(client, admin_bypass):
    """YAML dengan SLA lengkap → valid: true."""
    ac, _ = client
    res = await ac.post(
        "/contracts/validate-yaml",
        files={"file": ("ok.yaml", io.BytesIO(_minimal_yaml_sla()), "text/yaml")},
    )
    assert res.status_code == 200, res.text
    body = res.json()
    sla_errors = [e for e in body.get("errors", []) if "sla" in e.get("field", "")]
    assert sla_errors == [], sla_errors


@pytest.mark.asyncio
async def test_validate_rejects_missing_availability_start(client, admin_bypass):
    """YAML tanpa availability_start → error di validate-yaml."""
    ac, _ = client
    sla = {"availability_end": 18, "availability_unit": "h", "frequency": 4, "frequency_unit": "h"}
    res = await ac.post(
        "/contracts/validate-yaml",
        files={"file": ("t.yaml", io.BytesIO(_minimal_yaml_sla(sla=sla)), "text/yaml")},
    )
    body = res.json()
    assert body.get("valid") is False
    fields = [e["field"] for e in body.get("errors", [])]
    assert "metadata.sla.availability_start" in fields


@pytest.mark.asyncio
async def test_validate_rejects_missing_frequency_unit(client, admin_bypass):
    """YAML tanpa frequency_unit → error di validate-yaml."""
    ac, _ = client
    sla = {"availability_start": 6, "availability_end": 18, "availability_unit": "h", "frequency": 4}
    res = await ac.post(
        "/contracts/validate-yaml",
        files={"file": ("t.yaml", io.BytesIO(_minimal_yaml_sla(sla=sla)), "text/yaml")},
    )
    body = res.json()
    assert body.get("valid") is False
    fields = [e["field"] for e in body.get("errors", [])]
    assert "metadata.sla.frequency_unit" in fields


# ── POST /contracts/import-yaml ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_import_rejects_missing_sla(client, admin_bypass):
    """import-yaml tanpa SLA spec fields → 422."""
    ac, mocks = client
    mocks["dgr"].find_one.return_value = None

    sla = {"availability_end": 18, "availability_unit": "h"}  # incomplete
    res = await ac.post(
        "/contracts/import-yaml",
        files={"file": ("t.yaml", io.BytesIO(_minimal_yaml_sla(sla=sla)), "text/yaml")},
    )
    assert res.status_code == 422, res.text
    assert "sla" in res.json()["detail"].lower() or "availability_start" in res.json()["detail"]
    mocks["dgr"].insert_one.assert_not_called()


@pytest.mark.asyncio
async def test_import_accepts_complete_sla(client, admin_bypass):
    """import-yaml dengan SLA lengkap → 201."""
    ac, mocks = client
    mocks["dgr"].find_one.side_effect = [None, {"contract_number": "CN-SLA-TEST"}]

    res = await ac.post(
        "/contracts/import-yaml",
        files={"file": ("ok.yaml", io.BytesIO(_minimal_yaml_sla()), "text/yaml")},
    )
    assert res.status_code == 201, res.text
    mocks["dgr"].insert_one.assert_awaited_once()
