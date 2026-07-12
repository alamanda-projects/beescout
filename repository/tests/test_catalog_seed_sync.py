"""
Tests untuk perbendaharaan rule catalog + seed sync (issue #150).

Yang diuji:
- Semua modul di addons/catalog_rules/default.json valid terhadap
  RuleCatalogItem (termasuk dimensi baru: uniqueness, timeliness, consistency).
- 8 modul baru ala Sling hadir di katalog builtin.
- /catalog/seed perilaku lama: isi penuh saat kosong, 409 saat sudah ada isi.
- /catalog/seed?sync_missing=true: hanya menambah builtin yang belum ada,
  tidak menyentuh modul existing (builtin lama maupun custom), idempoten.
- YAML validator menerima 7 dimensi (satu sumber kebenaran dengan
  DIMENSION_TYPES) dan tetap menolak dimensi asal-asalan.
"""

import io

import pytest
import yaml as _yaml
from unittest.mock import AsyncMock, patch

from app.core.addon_loader import load_catalog_rules_addon
from app.model.rule_catalog import RuleCatalogItem

NEW_CODES = {
    "pattern_check", "enum_check", "range_check", "length_range_check",
    "unique_check", "row_count_range_check", "freshness_check", "custom_sql_check",
}


# ─── Katalog default.json ────────────────────────────────────────────────────

def test_default_catalog_parses_as_rule_catalog_items():
    rules = load_catalog_rules_addon()
    assert len(rules) >= 15
    # load_catalog_rules_addon sudah lewat RuleCatalogItem(**rule) — kalau ada
    # dimensi/param invalid, baris di atas raise. Validasi ulang eksplisit:
    for rule in rules:
        RuleCatalogItem(**rule)


def test_default_catalog_contains_sling_vocabulary():
    codes = {r["code"] for r in load_catalog_rules_addon()}
    assert NEW_CODES <= codes


def test_new_dimensions_used_by_builtin_rules():
    by_code = {r["code"]: r for r in load_catalog_rules_addon()}
    assert by_code["unique_check"]["dimension"] == "uniqueness"
    assert by_code["freshness_check"]["dimension"] == "timeliness"
    assert by_code["custom_sql_check"]["dimension"] == "consistency"


# ─── /catalog/seed ───────────────────────────────────────────────────────────

@pytest.fixture
def auth_root(client):
    from app.main import app
    from app.core.verificator import token_verification, access_verification

    async def fake_user():
        return {"usr": "root", "lvl": "root", "sts": True}

    async def fake_access(*args, **kwargs):
        return None

    app.dependency_overrides[token_verification] = fake_user
    app.dependency_overrides[access_verification] = fake_access
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def catalog_mock(client):
    cat = AsyncMock()
    with patch("app.main.catalogcollection", cat):
        yield cat


@pytest.mark.asyncio
async def test_seed_empty_collection_inserts_all(client, auth_root, catalog_mock):
    ac, _ = client
    catalog_mock.count_documents = AsyncMock(return_value=0)
    catalog_mock.insert_many = AsyncMock()

    resp = await ac.post("/catalog/seed")
    assert resp.status_code == 200
    catalog_mock.insert_many.assert_awaited_once()
    inserted = catalog_mock.insert_many.await_args.args[0]
    assert len(inserted) == len(load_catalog_rules_addon())


@pytest.mark.asyncio
async def test_seed_nonempty_collection_409(client, auth_root, catalog_mock):
    ac, _ = client
    catalog_mock.count_documents = AsyncMock(return_value=7)

    resp = await ac.post("/catalog/seed")
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_sync_missing_inserts_only_new_codes(client, auth_root, catalog_mock):
    ac, _ = client
    all_rules = load_catalog_rules_addon()
    legacy_codes = [r["code"] for r in all_rules if r["code"] not in NEW_CODES]
    # Instalasi lama: 7 builtin lama + 1 custom milik admin
    catalog_mock.distinct = AsyncMock(return_value=legacy_codes + ["my_custom_rule"])
    catalog_mock.insert_many = AsyncMock()

    resp = await ac.post("/catalog/seed", params={"sync_missing": "true"})
    assert resp.status_code == 200
    body = resp.json()
    assert set(body["added"]) == NEW_CODES

    inserted = catalog_mock.insert_many.await_args.args[0]
    assert {r["code"] for r in inserted} == NEW_CODES


@pytest.mark.asyncio
async def test_sync_missing_idempotent_when_complete(client, auth_root, catalog_mock):
    ac, _ = client
    catalog_mock.distinct = AsyncMock(
        return_value=[r["code"] for r in load_catalog_rules_addon()]
    )
    catalog_mock.insert_many = AsyncMock()

    resp = await ac.post("/catalog/seed", params={"sync_missing": "true"})
    assert resp.status_code == 200
    assert resp.json()["added"] == []
    catalog_mock.insert_many.assert_not_awaited()


# ─── YAML validator: dimensi baru ────────────────────────────────────────────

def _yaml_with_dataset_quality(dimension: str) -> bytes:
    doc = {
        "standard_version": "1.0.0",
        "contract_number": "CN-DIM-TEST",
        "metadata": {
            "name": "Test Kontrak",
            "owner": "Tim Test",
            "version": "1.0.0",
            "type": "CSV",
            "effective_date": "2024-01-01",
            "expiry_date": "2025-12-31",
            "description": {"purpose": "Analisis", "usage": "private"},
            "stakeholders": [
                {"name": "Tim Sales", "role": "consumer",
                 "email": "tim@example.com", "date_in": "2024-01-01"},
            ],
            "sla": {
                "availability_start": 6, "availability_end": 18,
                "availability_unit": "h", "frequency": 4,
                "frequency_unit": "h", "retention": 1, "retention_unit": "y",
            },
            "quality": [
                {"code": "freshness_check", "dimension": dimension,
                 "custom_properties": [
                     {"property": "max_age", "value": "24"},
                     {"property": "age_unit", "value": "jam"},
                 ]},
            ],
        },
        "model": [],
        "ports": [],
    }
    return _yaml.dump(doc, allow_unicode=True).encode("utf-8")


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


@pytest.mark.asyncio
@pytest.mark.parametrize("dim", ["uniqueness", "timeliness", "consistency"])
async def test_validate_yaml_accepts_new_dimensions(client, admin_bypass, dim):
    ac, _ = client
    res = await ac.post(
        "/contracts/validate-yaml",
        files={"file": ("t.yaml", io.BytesIO(_yaml_with_dataset_quality(dim)), "text/yaml")},
    )
    body = res.json()
    dim_errors = [e for e in body.get("errors") or [] if "dimension" in (e.get("field") or "")]
    assert dim_errors == [], dim_errors


@pytest.mark.asyncio
async def test_validate_yaml_rejects_unknown_dimension(client, admin_bypass):
    ac, _ = client
    res = await ac.post(
        "/contracts/validate-yaml",
        files={"file": ("t.yaml", io.BytesIO(_yaml_with_dataset_quality("kerapian")), "text/yaml")},
    )
    body = res.json()
    assert body.get("valid") is False
    assert any("dimension" in (e.get("field") or "") for e in body.get("errors", []))
