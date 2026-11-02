"""
Tests untuk blok `semantic` per kolom (#162 / ADR-0009).

Yang diuji:
- Backward compatibility: kontrak tanpa `semantic` tetap lolos apa adanya.
- Write-path /datacontract/add: enum `classification` ditegakkan (422 untuk
  nilai asing), nilai valid tersimpan utuh.
- Kontradiksi `is_pii` vs `classification` bersifat non-blocking (ADR-0009) —
  kontrak tetap tersimpan.
- YAML validator: enum jadi errors[], kontradiksi jadi warnings[].
- YAML import: enum ditegakkan (tidak bisa bypass lewat jalur import).
- ODCS converter: round-trip lossless + aturan derivasi satu arah
  classification/is_pii.
"""

import copy
import io

import pytest
import yaml as _yaml

from app.addons.converters.odcs import beescout_to_odcs, odcs_to_beescout

BASE_CONTRACT = {
    "standard_version": "1.0",
    "contract_number": "TESTSEM123",
    "metadata": {
        "version": "1.0.0",
        "type": "dataset",
        "name": "Test Kontrak Semantic",
        "owner": "tim_test",
        "effective_date": "2024-01-01",
        "expiry_date": "2025-12-31",
        "description": {"purpose": "Analisis pelanggan", "usage": "private"},
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

FULL_SEMANTIC = {
    "entity": "Customer",
    "concept": "Identifier",
    "canonical": True,
    "glossary": "CUSTOMER.ID",
    "classification": "pii",
}


def _contract(semantic=None, is_pii=True) -> dict:
    """Kontrak 1 kolom. `semantic=None` → kolom tanpa blok semantic sama sekali."""
    c = copy.deepcopy(BASE_CONTRACT)
    col = {
        "column": "uid",
        "logical_type": "string",
        "physical_type": "varchar(36)",
        "description": "id unik pelanggan",
        "is_pii": is_pii,
    }
    if semantic is not None:
        col["semantic"] = semantic
    c["model"] = [col]
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


# ─── Backward compatibility ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_add_accepts_contract_without_semantic(client, auth_bypass):
    """Inti ADR-0009: kontrak lama tanpa blok semantic tetap valid."""
    ac, mocks = client
    mocks["dgr"].find_one.return_value = None
    mocks["dgr"].insert_one.return_value = None
    res = await ac.post("/datacontract/add", json=_contract())
    assert res.status_code == 200, res.text
    saved = mocks["dgr"].insert_one.call_args[0][0]
    assert saved["model"][0]["semantic"] is None


@pytest.mark.asyncio
async def test_add_accepts_partial_semantic(client, auth_bypass):
    """Seluruh properti opsional — mengisi sebagian saja harus lolos."""
    ac, mocks = client
    mocks["dgr"].find_one.return_value = None
    mocks["dgr"].insert_one.return_value = None
    res = await ac.post("/datacontract/add", json=_contract({"entity": "Customer"}))
    assert res.status_code == 200, res.text
    saved = mocks["dgr"].insert_one.call_args[0][0]
    assert saved["model"][0]["semantic"]["entity"] == "Customer"
    assert saved["model"][0]["semantic"]["concept"] is None


# ─── Write-path /datacontract/add ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_add_persists_full_semantic(client, auth_bypass):
    ac, mocks = client
    mocks["dgr"].find_one.return_value = None
    mocks["dgr"].insert_one.return_value = None
    res = await ac.post("/datacontract/add", json=_contract(FULL_SEMANTIC))
    assert res.status_code == 200, res.text
    saved = mocks["dgr"].insert_one.call_args[0][0]
    assert saved["model"][0]["semantic"] == FULL_SEMANTIC


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "classification", ["public", "internal", "confidential", "sensitive", "pii"]
)
async def test_add_accepts_valid_classification(client, auth_bypass, classification):
    ac, mocks = client
    mocks["dgr"].find_one.return_value = None
    mocks["dgr"].insert_one.return_value = None
    is_pii = classification in ("pii", "sensitive")
    res = await ac.post(
        "/datacontract/add",
        json=_contract({"classification": classification}, is_pii=is_pii),
    )
    assert res.status_code == 200, res.text


@pytest.mark.asyncio
@pytest.mark.parametrize("classification", ["rahasia", "PII", "restricted", "top-secret"])
async def test_add_rejects_unknown_classification(client, auth_bypass, classification):
    ac, mocks = client
    mocks["dgr"].find_one.return_value = None
    res = await ac.post(
        "/datacontract/add", json=_contract({"classification": classification})
    )
    assert res.status_code == 422
    assert "classification" in res.json()["detail"]
    mocks["dgr"].insert_one.assert_not_called()


@pytest.mark.asyncio
async def test_add_allows_contradicting_is_pii(client, auth_bypass):
    """Kontradiksi is_pii vs classification = warning, bukan error (ADR-0009)."""
    ac, mocks = client
    mocks["dgr"].find_one.return_value = None
    mocks["dgr"].insert_one.return_value = None
    res = await ac.post(
        "/datacontract/add",
        json=_contract({"classification": "pii"}, is_pii=False),
    )
    assert res.status_code == 200, res.text
    mocks["dgr"].insert_one.assert_called_once()


@pytest.mark.asyncio
async def test_update_rejects_unknown_classification(client, auth_bypass):
    """Enum juga ditegakkan di /update — tidak ada pintu belakang lewat edit."""
    ac, mocks = client
    mocks["dgr"].find_one.return_value = {
        "contract_number": "TESTSEM123", "created_by": "tester", "managers": [],
    }
    res = await ac.put(
        "/datacontract/update?contract_number=TESTSEM123",
        json=_contract({"classification": "rahasia"}),
    )
    assert res.status_code == 422
    assert "classification" in res.json()["detail"]


# ─── YAML validate & import ──────────────────────────────────────────────────


@pytest.fixture
def admin_bypass(client):
    from app.main import app, require_admin

    async def fake_admin():
        return {"usr": "admin", "lvl": "admin", "sts": True}

    app.dependency_overrides[require_admin] = fake_admin
    yield
    app.dependency_overrides.clear()


def _yaml_file(contract: dict):
    body = _yaml.dump(contract, allow_unicode=True).encode("utf-8")
    return {"file": ("t.yaml", io.BytesIO(body), "text/yaml")}


@pytest.mark.asyncio
async def test_validate_yaml_flags_unknown_classification(client, admin_bypass):
    ac, _ = client
    res = await ac.post(
        "/contracts/validate-yaml", files=_yaml_file(_contract({"classification": "rahasia"}))
    )
    fields = [e.get("field") for e in res.json().get("errors") or []]
    assert "model[0].semantic.classification" in fields


@pytest.mark.asyncio
async def test_validate_yaml_warns_on_contradiction(client, admin_bypass):
    """Kontradiksi masuk warnings[], bukan errors[] — kontrak tetap valid."""
    ac, _ = client
    res = await ac.post(
        "/contracts/validate-yaml",
        files=_yaml_file(_contract({"classification": "pii"}, is_pii=False)),
    )
    body = res.json()
    assert body["valid"] is True
    warn_fields = [w.get("field") for w in body.get("warnings") or []]
    assert "model[0].semantic.classification" in warn_fields


@pytest.mark.asyncio
async def test_validate_yaml_accepts_valid_semantic(client, admin_bypass):
    ac, _ = client
    res = await ac.post("/contracts/validate-yaml", files=_yaml_file(_contract(FULL_SEMANTIC)))
    body = res.json()
    sem_errors = [e for e in body.get("errors") or [] if "semantic" in (e.get("field") or "")]
    assert sem_errors == []


@pytest.mark.asyncio
async def test_import_yaml_rejects_unknown_classification(client, admin_bypass):
    """Jalur import tidak boleh jadi bypass enum (mirrors /add)."""
    ac, mocks = client
    mocks["dgr"].reset_mock()
    res = await ac.post(
        "/contracts/import-yaml", files=_yaml_file(_contract({"classification": "rahasia"}))
    )
    assert res.status_code == 422
    assert "classification" in res.json()["detail"]
    mocks["dgr"].insert_one.assert_not_called()


# ─── ODCS round-trip ─────────────────────────────────────────────────────────


def test_odcs_roundtrip_preserves_semantic():
    contract = _contract(FULL_SEMANTIC)
    odcs = _yaml.safe_load(beescout_to_odcs(contract))
    prop = odcs["schema"][0]["properties"][0]

    # classification pakai slot ODCS native; sisanya ke customProperties.
    assert prop["classification"] == "pii"
    cp = {c["property"]: c["value"] for c in prop["customProperties"]}
    assert cp["semantic_entity"] == "Customer"
    assert cp["semantic_concept"] == "Identifier"
    assert cp["semantic_canonical"] is True
    assert cp["semantic_glossary"] == "CUSTOMER.ID"

    back, _ = odcs_to_beescout(odcs)
    assert back["model"][0]["semantic"] == FULL_SEMANTIC
    # Properti semantik tidak bocor jadi kolom top-level.
    assert "semantic_entity" not in back["model"][0]


def test_odcs_export_semantic_classification_wins_over_is_pii():
    """Derivasi satu arah (ADR-0009): semantic.classification menang."""
    contract = _contract({"classification": "internal"}, is_pii=True)
    odcs = _yaml.safe_load(beescout_to_odcs(contract))
    assert odcs["schema"][0]["properties"][0]["classification"] == "internal"


def test_odcs_export_falls_back_to_is_pii():
    """Tanpa blok semantic, perilaku lama tidak berubah: is_pii → confidential."""
    contract = _contract(is_pii=True)
    odcs = _yaml.safe_load(beescout_to_odcs(contract))
    assert odcs["schema"][0]["properties"][0]["classification"] == "confidential"


@pytest.mark.parametrize(
    "classification,expected_is_pii",
    [("pii", True), ("sensitive", True), ("confidential", True),
     ("internal", None), ("public", None)],
)
def test_odcs_import_derives_is_pii(classification, expected_is_pii):
    """Import mengisi is_pii dari classification. `confidential` ikut karena
    itulah nilai yang ditulis export untuk is_pii=true sejak #101 — tanpa itu
    round-trip kontrak lama jadi lossy."""
    odcs = _yaml.safe_load(beescout_to_odcs(_contract({"classification": classification})))
    back, _ = odcs_to_beescout(odcs)
    assert back["model"][0].get("is_pii") is expected_is_pii


@pytest.mark.parametrize("is_pii", [True, False])
def test_odcs_roundtrip_without_semantic_stays_clean(is_pii):
    """Kontrak tanpa semantic tidak boleh menumbuhkan blok semantic.

    Kasus is_pii=True yang penting: export menulis classification='confidential'
    sebagai derivasi, dan importer tidak boleh menganggapnya nilai eksplisit.
    """
    odcs = _yaml.safe_load(beescout_to_odcs(_contract(is_pii=is_pii)))
    back, _ = odcs_to_beescout(odcs)
    assert "semantic" not in back["model"][0]
    assert back["model"][0].get("is_pii") is (True if is_pii else None)


def test_odcs_roundtrip_keeps_explicit_confidential():
    """Beda dari kasus di atas: 'confidential' yang ditulis pengguna secara
    eksplisit harus bertahan, dibedakan lewat marker semantic_classification."""
    odcs = _yaml.safe_load(beescout_to_odcs(_contract({"classification": "confidential"})))
    back, _ = odcs_to_beescout(odcs)
    assert back["model"][0]["semantic"]["classification"] == "confidential"


def _foreign_odcs(classification: str) -> dict:
    """Dokumen ODCS pihak lain — tanpa customProperties BeeScout sama sekali."""
    return {
        "apiVersion": "v3.0.0", "kind": "DataContract", "id": "FOREIGN-1",
        "schema": [{
            "name": "customers",
            "properties": [{
                "name": "uid", "logicalType": "string",
                "physicalType": "varchar(36)", "description": "id",
                "classification": classification,
            }],
        }],
    }


@pytest.mark.parametrize(
    "classification,expected_semantic,expected_is_pii",
    [("pii", "pii", True), ("sensitive", "sensitive", True),
     ("internal", "internal", None), ("public", "public", None),
     # 'confidential' = nilai derivasi is_pii → tidak dipulihkan jadi semantic,
     # tapi informasinya tetap terbawa lewat is_pii.
     ("confidential", None, True)],
)
def test_odcs_import_foreign_doc(classification, expected_semantic, expected_is_pii):
    back, _ = odcs_to_beescout(_foreign_odcs(classification))
    col = back["model"][0]
    assert col.get("is_pii") is expected_is_pii
    assert (col.get("semantic") or {}).get("classification") == expected_semantic
