"""
Tests untuk converter BeeScout → Sling YAML (#155).

Framework (registry/endpoint) dicover test_converter_registry.py; di sini
hanya mapping-nya: flags/rule kolom → constraints, rule dataset → hooks,
rule tanpa padanan → blok komentar UNMAPPED, on_failure dari severity.
"""

import yaml
import pytest

from app.addons.converters.sling import beescout_to_sling
from app.addons.converters import registry


def _contract(**overrides) -> dict:
    base = {
        "contract_number": "CN-SLING-1",
        "metadata": {
            "name": "customer list",
            "quality": [
                {"code": "row_count_range_check", "severity": "high",
                 "custom_properties": [
                     {"property": "min_rows", "value": "1000"},
                     {"property": "max_rows", "value": "50000"},
                 ]},
                {"code": "freshness_check", "severity": "medium",
                 "custom_properties": [
                     {"property": "max_age", "value": "2"},
                     {"property": "age_unit", "value": "hari"},
                     {"property": "timestamp_column", "value": "updated_at"},
                 ]},
                {"code": "custom_sql_check",
                 "custom_properties": [
                     {"property": "query", "value": "SELECT COUNT(*) FROM t WHERE amount < 0"},
                     {"property": "expectation", "value": "= 0"},
                 ]},
                {"code": "pii_check",
                 "custom_properties": [{"property": "field_name", "value": "name"}]},
            ],
        },
        "model": [
            {"column": "uid", "logical_type": "string", "is_nullable": False,
             "quality": [
                 {"code": "pattern_check",
                  "custom_properties": [{"property": "pattern", "value": "^[0-9a-f-]{36}$"}]},
             ]},
            {"column": "status", "logical_type": "string",
             "quality": [
                 {"code": "enum_check",
                  "custom_properties": [
                      {"property": "allowed_values", "value": "active, pending, inactive"}]},
             ]},
            {"column": "amount", "logical_type": "decimal",
             "quality": [
                 {"code": "range_check",
                  "custom_properties": [{"property": "min_value", "value": "0"}]},
                 {"code": "string_check",
                  "custom_properties": [{"property": "contains_only", "value": "numeric"}]},
             ]},
        ],
    }
    base.update(overrides)
    return base


def _parse(out: str) -> dict:
    return yaml.safe_load(out)


# ─── Columns: flags + rule kolom → constraints ───────────────────────────────


def test_columns_constraints_mapping():
    doc = _parse(beescout_to_sling(_contract()))
    cols = doc["columns"]
    assert cols["uid"] == "string | value is not null and value ~ '^[0-9a-f-]{36}$'"
    assert cols["status"] == "string | value in ('active', 'pending', 'inactive')"
    assert cols["amount"].startswith("decimal | value >= 0")


def test_column_without_rules_is_type_only():
    c = _contract(model=[{"column": "note", "logical_type": "Text"}])
    doc = _parse(beescout_to_sling(c))
    assert doc["columns"]["note"] == "text"


def test_null_check_rule_dedupes_with_flag():
    c = _contract(model=[{
        "column": "uid", "logical_type": "string", "is_nullable": False,
        "quality": [{"code": "null_check", "custom_properties": []}],
    }])
    doc = _parse(beescout_to_sling(c))
    assert doc["columns"]["uid"].count("value is not null") == 1


# ─── Hooks: rule dataset ─────────────────────────────────────────────────────


def test_dataset_hooks_mapping():
    doc = _parse(beescout_to_sling(_contract()))
    hooks = doc["hooks"]["post"]

    row_count = next(h for h in hooks if "total_rows" in h.get("check", ""))
    assert row_count["check"] == "run.total_rows >= 1000 and run.total_rows <= 50000"
    assert row_count["on_failure"] == "abort"   # severity high → abort

    fresh = next(h for h in hooks if "freshness" in h.get("check", ""))
    assert "updated_at" in fresh["check"]
    assert "48" in fresh["check"]               # 2 hari → 48 jam
    assert fresh["on_failure"] == "warn"        # severity medium → warn

    query = next(h for h in hooks if h["type"] == "query")
    assert "SELECT COUNT(*)" in query["query"]
    assert "diharapkan: = 0" in query["query"]


def test_explicit_on_failure_field_wins_over_severity():
    # Forward-compat #151: field on_failure dipakai langsung bila ada.
    c = _contract(metadata={"name": "x", "quality": [
        {"code": "row_count_range_check", "severity": "high", "on_failure": "quiet",
         "custom_properties": [{"property": "min_rows", "value": "1"}]},
    ]}, model=[])
    doc = _parse(beescout_to_sling(c))
    assert doc["hooks"]["post"][0]["on_failure"] == "quiet"


# ─── UNMAPPED ────────────────────────────────────────────────────────────────


def test_unmapped_rules_listed_as_comments_not_dropped():
    out = beescout_to_sling(_contract())
    assert "# UNMAPPED" in out
    assert "dataset: pii_check" in out
    assert "kolom amount: string_check" in out
    # dan tidak bocor ke YAML yang di-parse
    doc = _parse(out)
    assert "pii_check" not in yaml.safe_dump(doc)


def test_no_unmapped_block_when_everything_maps():
    c = _contract(metadata={"name": "x", "quality": []},
                  model=[{"column": "uid", "logical_type": "string"}])
    assert "# UNMAPPED" not in beescout_to_sling(c)


# ─── Registry ────────────────────────────────────────────────────────────────


def test_registry_discovers_sling_export_only():
    conv = registry.get_converter("sling")
    assert conv is not None
    assert conv.can_export is True
    assert conv.can_import is False
    assert conv.file_extension == "sling.yaml"
