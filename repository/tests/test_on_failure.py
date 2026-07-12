"""
Tests untuk on_failure semantics (#151 / ADR-0008).

Yang diuji:
- Write-path /datacontract/add: enum on_failure ditegakkan — nilai asing 422,
  `skip` di rule dataset 422 (hanya bermakna di rule kolom), nilai valid lolos.
- YAML validator: mirror aturan yang sama (errors[], bukan HTTP error).
- ODCS converter: round-trip lossless via argument `beescout_on_failure`.
- Sling converter sudah dicover test_sling_converter.py
  (test_explicit_on_failure_field_wins_over_severity).
"""

import copy
import io

import pytest
import yaml as _yaml

from app.addons.converters.odcs import beescout_to_odcs, odcs_to_beescout

BASE_CONTRACT = {
    "standard_version": "1.0",
    "contract_number": "TESTOF123",
    "metadata": {
        "version": "1.0.0",
        "type": "dataset",
        "name": "Test Kontrak",
        "owner": "tim_test",
        "effective_date": "2024-01-01",
        "expiry_date": "2025-12-31",
        "description": {"purpose": "Analisis penjualan", "usage": "private"},
        "stakeholders": [{"name": "Tim Konsumen", "role": "consumer",
                          "email": "konsumen@example.com", "date_in": "2024-01-01"}],
        "sla": {"availability_start": 6, "availability_end": 18,
                "availability_unit": "h", "frequency": 4, "frequency_unit": "h"},
        "quality": [],
    },
    "model": [],
    "ports": [],
    "examples": {"type": None, "data": None},
}


def _contract(dataset_of=None, column_of=None) -> dict:
    c = copy.deepcopy(BASE_CONTRACT)
    if dataset_of is not None:
        c["metadata"]["quality"] = [{
            "code": "row_count_range_check", "dimension": "completeness",
            "severity": "high", "on_failure": dataset_of,
            "custom_properties": [{"property": "min_rows", "value": "1"}],
        }]
    if column_of is not None:
        c["model"] = [{
            "column": "uid", "logical_type": "string",
            "physical_type": "varchar(36)", "description": "id unik",
            "quality": [{"code": "pattern_check", "dimension": "validity",
                         "on_failure": column_of,
                         "custom_properties": [{"property": "pattern", "value": "^x$"}]}],
        }]
    return c


@pytest.fixture
def auth_bypass(client):
    from app.main import app
    from app.core.verificator import token_verification, access_verification

    _, mocks = client
    mocks["dgr"].reset_mock()

    async def fake_user():
        return {"usr": "tester", "lvl": "admin", "sts": True}

    async def fake_access(*args, **kwargs):
        return None

    app.dependency_overrides[token_verification] = fake_user
    app.dependency_overrides[access_verification] = fake_access
    yield
    app.dependency_overrides.clear()


# ─── Write-path /datacontract/add ────────────────────────────────────────────


@pytest.mark.asyncio
@pytest.mark.parametrize("dataset_of,column_of", [
    ("abort", None), ("warn", None), ("quiet", None),
    (None, "skip"), (None, "abort"),
    ("warn", "skip"),
])
async def test_add_accepts_valid_on_failure(client, auth_bypass, dataset_of, column_of):
    ac, mocks = client
    mocks["dgr"].find_one.return_value = None
    mocks["dgr"].insert_one.return_value = None
    res = await ac.post("/datacontract/add", json=_contract(dataset_of, column_of))
    assert res.status_code == 200, res.text


@pytest.mark.asyncio
async def test_add_rejects_skip_on_dataset_rule(client, auth_bypass):
    """`skip` tidak bermakna di rule dataset (ADR-0008) → 422."""
    ac, mocks = client
    mocks["dgr"].find_one.return_value = None
    res = await ac.post("/datacontract/add", json=_contract(dataset_of="skip"))
    assert res.status_code == 422
    assert "skip" in res.json()["detail"]
    mocks["dgr"].insert_one.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize("dataset_of,column_of", [("meledak", None), (None, "retry")])
async def test_add_rejects_unknown_on_failure(client, auth_bypass, dataset_of, column_of):
    ac, mocks = client
    mocks["dgr"].find_one.return_value = None
    res = await ac.post("/datacontract/add", json=_contract(dataset_of, column_of))
    assert res.status_code == 422
    mocks["dgr"].insert_one.assert_not_called()


# ─── YAML validator ──────────────────────────────────────────────────────────


@pytest.fixture
def admin_bypass(client):
    from app.main import app, require_admin

    async def fake_admin():
        return {"usr": "admin", "lvl": "admin", "sts": True}

    app.dependency_overrides[require_admin] = fake_admin
    yield
    app.dependency_overrides.clear()


async def _validate(ac, contract: dict) -> dict:
    body = _yaml.dump(contract, allow_unicode=True).encode("utf-8")
    res = await ac.post(
        "/contracts/validate-yaml",
        files={"file": ("t.yaml", io.BytesIO(body), "text/yaml")},
    )
    return res.json()


@pytest.mark.asyncio
async def test_validate_yaml_flags_skip_on_dataset(client, admin_bypass):
    ac, _ = client
    body = await _validate(ac, _contract(dataset_of="skip"))
    fields = [e.get("field") for e in body.get("errors") or []]
    assert "metadata.quality[0].on_failure" in fields


@pytest.mark.asyncio
async def test_validate_yaml_accepts_skip_on_column(client, admin_bypass):
    ac, _ = client
    body = await _validate(ac, _contract(column_of="skip"))
    of_errors = [e for e in body.get("errors") or []
                 if "on_failure" in (e.get("field") or "")]
    assert of_errors == []


# ─── ODCS round-trip ─────────────────────────────────────────────────────────


def test_odcs_roundtrip_preserves_on_failure():
    contract = _contract(dataset_of="quiet", column_of="skip")
    odcs = _yaml.safe_load(beescout_to_odcs(contract))

    # Export: tersimpan sebagai argument beescout_on_failure (tidak ada slot ODCS).
    assert odcs["quality"][0]["arguments"]["beescout_on_failure"] == "quiet"

    back, _ = odcs_to_beescout(odcs)
    assert back["metadata"]["quality"][0]["on_failure"] == "quiet"
    assert back["model"][0]["quality"][0]["on_failure"] == "skip"
    # Argument internal tidak bocor jadi custom_properties.
    props = {cp["property"] for cp in back["metadata"]["quality"][0]["custom_properties"]}
    assert "beescout_on_failure" not in props
