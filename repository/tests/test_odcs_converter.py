"""Tests untuk converter ODCS — #101 (export) + #100 (import + round-trip).

Memverifikasi:
- `beescout_to_odcs`: pemetaan field overlap ke ODCS v3 + preservasi field
  BeeScout-specific di customProperties (non-lossy).
- `odcs_to_beescout`: rekonstruksi BeeScout dari ODCS + warning untuk field
  yang di-drop / default.
- Round-trip BeeScout→ODCS→BeeScout = identik (modulo nilai kosong).

Mengikuti data-contract/docs/comparison-odcs.md.
"""

import yaml

# #154: converter ODCS pindah ke add-on converters.
from app.addons.converters.odcs import beescout_to_odcs, odcs_to_beescout, _clean


def _sample_contract() -> dict:
    return {
        "standard_version": "0.5.0",
        "contract_number": "CN-ABC123",
        "metadata": {
            "version": "1.0.0",
            "type": "CSV",
            "name": "Penjualan Harian",
            "owner": "tim-data",
            "consumption_mode": "Analytical",
            "effective_date": "2026-01-01",
            "expiry_date": "2026-12-31",
            "description": {"purpose": "Analisis penjualan", "usage": "private"},
            "sla": {
                "availability_start": 0,
                "availability_end": 23,
                "availability_unit": "h",
                "frequency": 1,
                "frequency_unit": "d",
                "frequency_cron": "0 6 * * *",
                "retention": 5,
                "retention_unit": "tahun",
            },
            "stakeholders": [
                {
                    "name": "John Doe",
                    "role": "owner",
                    "email": "john@example.com",
                    "username": "johnd",
                    "date_in": "2026-01-01",
                },
                {"name": "Tim Analitik", "role": "consumer", "email": "analytics@example.com"},
            ],
            "consumer": [{"name": "Tim BI", "use_case": "dashboard mingguan"}],
            "quality": [
                {
                    "code": "QR001",
                    "dimension": "completeness",
                    "impact": "operational",
                    "severity": "high",
                    "custom_properties": [{"property": "threshold", "value": "0.95"}],
                }
            ],
            "contract_reference": [{"number": "TICKET-1", "type": "Tiket Permintaan Data"}],
        },
        "model": [
            {
                "column": "id",
                "business_name": "ID Transaksi",
                "logical_type": "UUID",
                "physical_type": "VARCHAR(36)",
                "description": "Primary key",
                "is_primary": True,
                "is_nullable": False,
                "is_pii": True,
                "is_clustered": True,
                "is_audit": False,
            }
        ],
        "ports": [{"object": "source", "properties": [{"property": "host", "value": "db1"}]}],
    }


def _parse(contract: dict) -> dict:
    return yaml.safe_load(beescout_to_odcs(contract))


def test_top_level_mapping():
    odcs = _parse(_sample_contract())
    assert odcs["apiVersion"] == "v3.0.0"
    assert odcs["kind"] == "DataContract"
    assert odcs["id"] == "CN-ABC123"
    assert odcs["name"] == "Penjualan Harian"
    assert odcs["version"] == "1.0.0"
    assert odcs["description"]["purpose"] == "Analisis penjualan"
    assert odcs["description"]["usage"] == "private"


def test_schema_and_column_mapping():
    odcs = _parse(_sample_contract())
    props = odcs["schema"][0]["properties"]
    col = props[0]
    assert col["name"] == "id"
    assert col["businessName"] == "ID Transaksi"
    assert col["logicalType"] == "UUID"
    assert col["physicalType"] == "VARCHAR(36)"
    assert col["primaryKey"] is True
    # is_nullable False → required True (inversi)
    assert col["required"] is True
    # is_pii True → classification confidential
    assert col["classification"] == "confidential"
    # BeeScout-specific flags disimpan di customProperties kolom
    cp = {c["property"]: c["value"] for c in col["customProperties"]}
    assert cp["is_clustered"] is True
    # is_audit False bermakna → tetap dipertahankan (bukan di-drop)
    assert cp["is_audit"] is False


def test_required_inversion_nullable_true():
    c = _sample_contract()
    c["model"][0]["is_nullable"] = True
    col = _parse(c)["schema"][0]["properties"][0]
    assert col["required"] is False


def test_team_members_mapping():
    odcs = _parse(_sample_contract())
    members = odcs["team"]["members"]
    assert members[0]["name"] == "John Doe"
    assert members[0]["role"] == "owner"
    assert members[0]["username"] == "johnd"
    # username fallback ke email bila username kosong
    assert members[1]["username"] == "analytics@example.com"


def test_sla_and_lifecycle_in_service_level_agreements():
    odcs = _parse(_sample_contract())
    sla = {x["property"]: x["value"] for x in odcs["serviceLevelAgreements"]}
    assert sla["availabilityStart"] == 0     # nilai 0 tidak boleh hilang
    assert sla["availabilityEnd"] == 23
    assert sla["frequency"] == 1
    assert sla["retention"] == 5
    assert sla["effectiveDate"] == "2026-01-01"
    assert sla["expiryDate"] == "2026-12-31"


def test_quality_mapping():
    odcs = _parse(_sample_contract())
    q = odcs["quality"][0]
    assert q["id"] == "QR001"
    assert q["dimension"] == "completeness"
    assert q["businessImpact"] == "operational"   # impact → businessImpact
    assert q["severity"] == "high"
    assert q["arguments"]["threshold"] == "0.95"


def test_authoritative_definitions_from_contract_reference():
    odcs = _parse(_sample_contract())
    ad = odcs["authoritativeDefinitions"][0]
    assert ad["url"] == "TICKET-1"
    assert ad["type"] == "Tiket Permintaan Data"


def test_beescout_specific_preserved_in_custom_properties():
    odcs = _parse(_sample_contract())
    cp = {c["property"]: c["value"] for c in odcs["customProperties"]}
    assert cp["standard_version"] == "0.5.0"
    assert cp["contract_number"] == "CN-ABC123"
    assert cp["consumption_mode"] == "Analytical"
    assert cp["frequency_cron"] == "0 6 * * *"
    # consumer[] & ports[] documentary/BeeScout-only — tetap utuh
    assert cp["consumer"][0]["name"] == "Tim BI"
    assert cp["ports"][0]["object"] == "source"


def test_minimal_contract_does_not_crash():
    odcs = _parse({"contract_number": "CN-MIN", "metadata": {"name": "Minimal"}})
    assert odcs["id"] == "CN-MIN"
    assert odcs["name"] == "Minimal"
    # tidak ada schema/team/quality kosong yang ter-emit
    assert "schema" not in odcs
    assert "quality" not in odcs


def test_output_has_header_comment():
    out = beescout_to_odcs(_sample_contract())
    assert out.startswith("# Data contract di-export dari BeeScout ke format ODCS v3.")


# ─── Import (ODCS → BeeScout) ────────────────────────────────────────────────

def test_round_trip_beescout_odcs_beescout():
    """Export lalu import harus mengembalikan kontrak yang identik (lossless)."""
    original = _sample_contract()
    odcs_dict = yaml.safe_load(beescout_to_odcs(original))
    rebuilt, warnings = odcs_to_beescout(odcs_dict)
    assert rebuilt == _clean(original)
    # round-trip kontrak hasil export sendiri → tidak ada warning drop
    assert warnings == []


def test_import_minimal_odcs_external():
    odcs = {
        "apiVersion": "v3.0.0",
        "kind": "DataContract",
        "id": "ext-1",
        "name": "External Contract",
        "version": "2.0.0",
    }
    bs, warnings = odcs_to_beescout(odcs)
    assert bs["contract_number"] == "ext-1"
    assert bs["metadata"]["name"] == "External Contract"
    assert bs["metadata"]["version"] == "2.0.0"
    # standard_version tidak ada → default + warning
    assert bs["standard_version"] == "0.0.0"
    assert any("standard_version" in w for w in warnings)


def test_import_drops_odcs_specific_with_warning():
    odcs = {
        "id": "x", "name": "X",
        "tenant": "acme", "status": "production", "price": {"amount": 10},
        "customProperties": [{"property": "standard_version", "value": "0.5.0"}],
    }
    _, warnings = odcs_to_beescout(odcs)
    assert any("tenant" in w for w in warnings)
    assert any("status" in w for w in warnings)
    assert any("price" in w for w in warnings)


def test_import_external_username_holds_email():
    """ODCS eksternal: username berisi email → email BeeScout ter-isi."""
    odcs = {
        "id": "x", "name": "X",
        "team": {"members": [{"name": "Jane", "role": "consumer", "username": "jane@corp.com"}]},
    }
    bs, _ = odcs_to_beescout(odcs)
    s = bs["metadata"]["stakeholders"][0]
    assert s["email"] == "jane@corp.com"


def test_import_required_inversion():
    odcs = {
        "id": "x", "name": "X",
        "schema": [{"name": "t", "properties": [
            {"name": "col_a", "required": True},
            {"name": "col_b", "required": False},
        ]}],
    }
    cols = {c["column"]: c for c in odcs_to_beescout(odcs)[0]["model"]}
    assert cols["col_a"]["is_nullable"] is False
    assert cols["col_b"]["is_nullable"] is True


def test_imported_contract_validates_against_all_model():
    """Regresi: hasil import harus lolos model `All` (ports/examples Optional)
    agar tidak 500 saat dibaca via /datacontract/filter."""
    from app.model.all import All
    bs, _ = odcs_to_beescout(yaml.safe_load(beescout_to_odcs(_sample_contract())))
    model = All(**bs)  # tidak boleh raise meski examples kosong
    # examples tidak ada di sample → Optional, tidak memicu 500 saat dibaca
    assert model.examples is None


def test_import_multi_schema_warns_and_flattens_first():
    odcs = {
        "id": "x", "name": "X",
        "schema": [
            {"name": "t1", "properties": [{"name": "a"}]},
            {"name": "t2", "properties": [{"name": "b"}]},
        ],
    }
    bs, warnings = odcs_to_beescout(odcs)
    assert [c["column"] for c in bs["model"]] == ["a"]
    assert any("schema" in w.lower() for w in warnings)
