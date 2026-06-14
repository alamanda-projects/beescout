"""
Converter BeeScout ↔ ODCS (Open Data Contract Standard v3).

Pemetaan field mengikuti `data-contract/docs/comparison-odcs.md` (#99). Modul
ini sengaja menampung exporter (#101) dan — menyusul — importer (#100) di satu
file supaya mapping tidak drift saat round-trip.

Prinsip export (`beescout_to_odcs`):
- Field yang overlap dipetakan ke padanan ODCS-nya (id, name, schema/properties,
  team/members, serviceLevelAgreements, quality, authoritativeDefinitions).
- Field BeeScout-specific (consumer[], consumption_mode, frequency_cron,
  ports[], is_clustered/is_audit, examples, dll) TIDAK di-drop — disimpan di
  `customProperties` supaya non-lossy & ramah round-trip. Header comment YAML
  mencatat hal ini.
- Keputusan atas open-questions di comparison-odcs.md:
  * `ports[].object` (source/destination): disimpan utuh di customProperties
    (bukan di-drop) agar tidak lossy.
  * `stakeholders[].role: reviewer`: diteruskan apa adanya (ODCS role = free string).
  * `is_nullable` → ODCS `required` (inversi, sesuai mapping doc); `is_mandatory`
    disimpan di customProperties kolom untuk menghindari ambiguitas.
"""
from __future__ import annotations

import yaml

ODCS_API_VERSION = "v3.0.0"
ODCS_KIND = "DataContract"

_EMPTY = (None, "", [], {})


def _clean(value):
    """Buang key/elemen dengan value kosong (None/''/[]/{}) secara rekursif.

    Nilai falsy yang bermakna (0, False) sengaja dipertahankan — penting untuk
    field seperti `availability_start: 0` atau `required: false`.
    """
    if isinstance(value, dict):
        return {k: _clean(v) for k, v in value.items() if _clean(v) not in _EMPTY}
    if isinstance(value, list):
        return [_clean(v) for v in value if _clean(v) not in _EMPTY]
    return value


def _custom_props(pairs):
    """Bentuk list customProperties ODCS dari (property, value), skip yang kosong."""
    return [{"property": p, "value": v} for p, v in pairs if v not in _EMPTY]


def _map_quality(q: dict) -> dict:
    """metadata.quality[] / model[].quality[] → item ODCS quality[]."""
    arguments = {}
    for cp in (q.get("custom_properties") or []):
        if isinstance(cp, dict) and cp.get("property"):
            arguments[cp["property"]] = cp.get("value")
    return _clean({
        "id": q.get("code"),
        "description": q.get("description"),
        "dimension": q.get("dimension"),
        "businessImpact": q.get("impact"),   # ADR-0003: impact → businessImpact
        "severity": q.get("severity"),
        "arguments": arguments,
    })


def _map_column(col: dict) -> dict:
    nullable = col.get("is_nullable")
    return _clean({
        "name": col.get("column"),
        "businessName": col.get("business_name"),
        "logicalType": col.get("logical_type"),
        "physicalType": col.get("physical_type"),
        "description": col.get("description"),
        "primaryKey": col.get("is_primary"),
        # ODCS required = inversi is_nullable (comparison-odcs.md). None → biarkan kosong.
        "required": (not nullable) if nullable is not None else None,
        "partitioned": col.get("is_partition"),
        "classification": "confidential" if col.get("is_pii") else None,
        "tags": col.get("tags"),
        "examples": col.get("sample_value"),
        "quality": [_map_quality(q) for q in (col.get("quality") or [])],
        # BeeScout-specific flags — simpan agar non-lossy.
        "customProperties": _custom_props([
            ("is_clustered", col.get("is_clustered")),
            ("is_audit", col.get("is_audit")),
            ("is_mandatory", col.get("is_mandatory")),
        ]),
    })


def beescout_to_odcs(contract: dict) -> str:
    """Konversi satu kontrak BeeScout (dict) → string YAML ODCS v3."""
    meta = contract.get("metadata") or {}
    desc = meta.get("description") or {}
    sla = meta.get("sla") or {}

    # schema[] — BeeScout model[] flat dibungkus 1 ODCS schema object.
    properties = [_map_column(c) for c in (contract.get("model") or [])]
    schema = []
    if properties:
        schema = [_clean({
            "name": meta.get("name") or contract.get("contract_number"),
            "physicalType": meta.get("type"),
            "properties": properties,
        })]

    # team.members[] — dari stakeholders[].
    members = [
        _clean({
            "name": s.get("name"),
            "username": s.get("username") or s.get("email"),
            "role": s.get("role"),
            "dateIn": s.get("date_in"),
            "dateOut": s.get("date_out"),
        })
        for s in (meta.get("stakeholders") or [])
    ]

    # serviceLevelAgreements[] — SLA + lifecycle (effective/expiry).
    sla_list = _custom_props([
        ("availabilityStart", sla.get("availability_start")),
        ("availabilityEnd", sla.get("availability_end")),
        ("availabilityUnit", sla.get("availability_unit")),
        ("frequency", sla.get("frequency")),
        ("frequencyUnit", sla.get("frequency_unit")),
        ("retention", sla.get("retention")),
        ("retentionUnit", sla.get("retention_unit")),
        ("effectiveDate", meta.get("effective_date")),
        ("expiryDate", meta.get("expiry_date")),
    ])

    quality = [_map_quality(q) for q in (meta.get("quality") or [])]

    # authoritativeDefinitions[] — dari contract_reference[] {number, type}.
    auth_defs = [
        _clean({"url": ref.get("number"), "type": ref.get("type")})
        for ref in (meta.get("contract_reference") or [])
        if isinstance(ref, dict)
    ]

    # customProperties top-level — semua field BeeScout-specific (non-lossy).
    top_custom = _custom_props([
        ("standard_version", contract.get("standard_version")),
        ("contract_number", contract.get("contract_number")),
        ("consumption_mode", meta.get("consumption_mode")),
        ("frequency_cron", sla.get("frequency_cron")),
        ("prev_contract", meta.get("prev_contract")),
        ("consumer", meta.get("consumer")),
        ("ports", contract.get("ports")),
        ("examples", contract.get("examples")),
    ])

    odcs = _clean({
        "apiVersion": ODCS_API_VERSION,
        "kind": ODCS_KIND,
        "id": contract.get("contract_number"),
        "name": meta.get("name"),
        "version": meta.get("version"),
        "description": {"purpose": desc.get("purpose"), "usage": desc.get("usage")},
        "schema": schema,
        "team": {"members": members},
        "serviceLevelAgreements": sla_list,
        "quality": quality,
        "authoritativeDefinitions": auth_defs,
        "customProperties": top_custom,
    })

    header = (
        "# Data contract di-export dari BeeScout ke format ODCS v3.\n"
        "# Field BeeScout-specific (consumer, consumption_mode, frequency_cron,\n"
        "# ports, is_clustered/is_audit, examples) disimpan di customProperties\n"
        "# agar tidak hilang. Pemetaan: data-contract/docs/comparison-odcs.md\n"
    )
    body = yaml.safe_dump(odcs, sort_keys=False, allow_unicode=True, default_flow_style=False)
    return header + body
