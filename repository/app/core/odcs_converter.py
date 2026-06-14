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

    # team.members[] — dari stakeholders[]. `username` diisi username-atau-email
    # (interop ODCS), tapi nilai asli BeeScout (email + username) ikut disimpan di
    # member.customProperties supaya round-trip lossless.
    members = [
        _clean({
            "name": s.get("name"),
            "username": s.get("username") or s.get("email"),
            "role": s.get("role"),
            "dateIn": s.get("date_in"),
            "dateOut": s.get("date_out"),
            "customProperties": _custom_props([
                ("email", s.get("email")),
                ("beescout_username", s.get("username")),
            ]),
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
        # owner & type tidak punya slot ODCS yang lossless → simpan di sini juga
        # supaya import (#100) bisa merekonstruksi tanpa kehilangan.
        ("owner", meta.get("owner")),
        ("metadata_type", meta.get("type")),
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


# ─── Import: ODCS → BeeScout (#100) ──────────────────────────────────────────

# Default standard_version untuk ODCS yang tidak membawa customProperties dari
# BeeScout (mis. kontrak ODCS eksternal). Sengaja konservatif.
DEFAULT_STANDARD_VERSION = "0.0.0"

# Field top-level ODCS yang tidak punya padanan BeeScout → di-drop saat import.
_ODCS_ONLY_TOPLEVEL = ("tenant", "domain", "status", "support", "price", "dataProduct")


def _cp_to_dict(custom_properties) -> dict:
    """customProperties ODCS (list {property,value}) → dict {property: value}."""
    out = {}
    for cp in (custom_properties or []):
        if isinstance(cp, dict) and cp.get("property") is not None:
            out[cp["property"]] = cp.get("value")
    return out


def _quality_odcs_to_beescout(q: dict) -> dict:
    args = q.get("arguments") or {}
    custom_properties = [{"property": k, "value": v} for k, v in args.items()]
    return _clean({
        "code": q.get("id") or q.get("metric"),
        "description": q.get("description"),
        "dimension": q.get("dimension"),
        "impact": q.get("businessImpact"),   # businessImpact → impact (ADR-0003)
        "severity": q.get("severity"),
        "custom_properties": custom_properties,
    })


def _column_odcs_to_beescout(prop: dict) -> dict:
    cp = _cp_to_dict(prop.get("customProperties"))
    required = prop.get("required")
    return _clean({
        "column": prop.get("name"),
        "business_name": prop.get("businessName"),
        "logical_type": prop.get("logicalType"),
        "physical_type": prop.get("physicalType"),
        "description": prop.get("description"),
        "is_primary": prop.get("primaryKey"),
        # required → is_nullable (inversi balik). None → biarkan kosong.
        "is_nullable": (not required) if required is not None else None,
        "is_partition": prop.get("partitioned"),
        "is_pii": True if prop.get("classification") == "confidential" else None,
        "sample_value": prop.get("examples"),
        "tags": prop.get("tags"),
        "quality": [_quality_odcs_to_beescout(q) for q in (prop.get("quality") or [])],
        # flag BeeScout-specific yang disimpan saat export.
        "is_clustered": cp.get("is_clustered"),
        "is_audit": cp.get("is_audit"),
        "is_mandatory": cp.get("is_mandatory"),
    })


def odcs_to_beescout(odcs: dict) -> tuple[dict, list[str]]:
    """Konversi dict ODCS v3 → (kontrak BeeScout dict, list warning).

    Mengembalikan dict (bukan Pydantic) — caller (endpoint import) yang
    memvalidasi via model `All`. Field BeeScout-specific yang sebelumnya
    disimpan di customProperties (hasil export BeeScout) direkonstruksi penuh
    sehingga round-trip lossless. ODCS eksternal yang tidak punya field wajib
    BeeScout akan lolos converter tapi gagal validasi Pydantic di endpoint (422).
    """
    warnings: list[str] = []
    cp = _cp_to_dict(odcs.get("customProperties"))
    sla_props = _cp_to_dict(odcs.get("serviceLevelAgreements"))

    schemas = odcs.get("schema") or []
    if len(schemas) > 1:
        warnings.append(
            "ODCS memiliki >1 objek schema; hanya objek pertama yang di-flatten "
            "ke model[] BeeScout (BeeScout flat, bukan hierarkis)."
        )
    first_schema = schemas[0] if schemas else {}

    # stakeholders[] dari team.members[] — utamakan nilai asli di customProperties.
    stakeholders = []
    for m in ((odcs.get("team") or {}).get("members") or []):
        mcp = _cp_to_dict(m.get("customProperties"))
        username = mcp.get("beescout_username")
        email = mcp.get("email")
        # ODCS eksternal: username bisa berisi email. Fallback bila CP kosong.
        if email is None and isinstance(m.get("username"), str) and "@" in m["username"]:
            email = m["username"]
        if username is None and m.get("username") and m["username"] != email:
            username = m["username"]
        stakeholders.append(_clean({
            "name": m.get("name"),
            "role": m.get("role"),
            "email": email,
            "username": username,
            "date_in": m.get("dateIn"),
            "date_out": m.get("dateOut"),
        }))

    metadata = _clean({
        "version": odcs.get("version"),
        "type": cp.get("metadata_type") or first_schema.get("physicalType"),
        "name": odcs.get("name"),
        "owner": cp.get("owner"),
        "consumption_mode": cp.get("consumption_mode"),
        "effective_date": sla_props.get("effectiveDate"),
        "expiry_date": sla_props.get("expiryDate"),
        "description": {
            "purpose": (odcs.get("description") or {}).get("purpose"),
            "usage": (odcs.get("description") or {}).get("usage"),
        },
        "sla": {
            "availability_start": sla_props.get("availabilityStart"),
            "availability_end": sla_props.get("availabilityEnd"),
            "availability_unit": sla_props.get("availabilityUnit"),
            "frequency": sla_props.get("frequency"),
            "frequency_unit": sla_props.get("frequencyUnit"),
            "retention": sla_props.get("retention"),
            "retention_unit": sla_props.get("retentionUnit"),
            "frequency_cron": cp.get("frequency_cron"),
        },
        "stakeholders": stakeholders,
        "consumer": cp.get("consumer") or [],
        "quality": [_quality_odcs_to_beescout(q) for q in (odcs.get("quality") or [])],
        "contract_reference": [
            _clean({"number": ad.get("url"), "type": ad.get("type")})
            for ad in (odcs.get("authoritativeDefinitions") or [])
            if isinstance(ad, dict)
        ],
        "prev_contract": cp.get("prev_contract"),
    })

    contract = _clean({
        "standard_version": cp.get("standard_version") or DEFAULT_STANDARD_VERSION,
        "contract_number": cp.get("contract_number") or odcs.get("id"),
        "metadata": metadata,
        "model": [_column_odcs_to_beescout(p) for p in (first_schema.get("properties") or [])],
        "ports": cp.get("ports") or [],
        "examples": cp.get("examples"),
    })

    # Warning untuk field ODCS yang sengaja di-drop (tak ada padanan BeeScout).
    for k in _ODCS_ONLY_TOPLEVEL:
        if odcs.get(k) not in _EMPTY:
            warnings.append(f"Field ODCS '{k}' tidak punya padanan BeeScout — di-drop.")
    if not cp.get("standard_version"):
        warnings.append(
            f"standard_version tidak ada di ODCS — diisi default '{DEFAULT_STANDARD_VERSION}'."
        )

    return contract, warnings
