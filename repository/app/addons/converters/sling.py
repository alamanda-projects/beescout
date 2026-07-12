"""
Converter BeeScout → Sling YAML (data quality) — export-only (#155).

Menerjemahkan kontrak BeeScout menjadi konfigurasi kualitas data ala Sling
(https://docs.slingdata.io/concepts/data-quality). Dua lapisan sumber dibaca
(#154 — constraint struktural vs pemeriksaan berkala):

1. Flag model + rule kolom → Sling column constraints
   (`kolom: tipe | value is not null and value ~ '...'`).
2. Rule dataset → Sling hooks (`check` untuk row count/freshness,
   `query` untuk SQL kustom).

Prinsip non-lossy versi export-only: rule tanpa padanan Sling (pii_check,
distinct_check, dll.) TIDAK di-drop diam-diam — dicantumkan sebagai blok
komentar `# UNMAPPED` di akhir file agar engineer melihatnya.

`on_failure` hook: bila rule membawa field `on_failure` (menyusul di #151)
dipakai langsung; selain itu fallback dari severity (high → abort, sisanya
warn) — didokumentasikan di header output.
"""
from __future__ import annotations

import yaml

# Peta rule kolom → builder ekspresi constraint Sling.
# Rule kolom di luar peta ini masuk blok UNMAPPED.
_COLUMN_RULE_CODES = {"pattern_check", "enum_check", "range_check", "null_check"}

# Rule dataset yang diterjemahkan jadi hooks; sisanya UNMAPPED.
_DATASET_RULE_CODES = {"row_count_range_check", "freshness_check", "custom_sql_check"}

_AGE_UNIT_HOURS = {"jam": 1, "hari": 24, "pekan": 24 * 7}


def _params(q: dict) -> dict:
    """custom_properties [{property,value}] → dict. Key ganda: nilai digabung list."""
    out: dict = {}
    for cp in (q.get("custom_properties") or []):
        if not (isinstance(cp, dict) and cp.get("property")):
            continue
        key, val = cp["property"], cp.get("value")
        if key in out:
            prev = out[key] if isinstance(out[key], list) else [out[key]]
            out[key] = prev + [val]
        else:
            out[key] = val
    return out


def _on_failure(q: dict) -> str:
    # Forward-compatible dengan #151; fallback severity sampai field itu ada.
    explicit = q.get("on_failure")
    if explicit in ("abort", "warn", "skip", "quiet"):
        return explicit
    return "abort" if q.get("severity") == "high" else "warn"


def _column_constraints(col: dict) -> tuple[list[str], list[str]]:
    """(daftar ekspresi constraint, daftar rule unmapped) untuk satu kolom."""
    constraints: list[str] = []
    unmapped: list[str] = []

    if col.get("is_nullable") is False:
        constraints.append("value is not null")

    for q in (col.get("quality") or []):
        code = q.get("code")
        p = _params(q)
        if code == "null_check":
            if "value is not null" not in constraints:
                constraints.append("value is not null")
        elif code == "pattern_check" and p.get("pattern"):
            constraints.append(f"value ~ '{p['pattern']}'")
        elif code == "enum_check" and p.get("allowed_values"):
            values = [v.strip() for v in str(p["allowed_values"]).split(",") if v.strip()]
            quoted = ", ".join(f"'{v}'" for v in values)
            constraints.append(f"value in ({quoted})")
        elif code == "range_check":
            if p.get("min_value") not in (None, ""):
                constraints.append(f"value >= {p['min_value']}")
            if p.get("max_value") not in (None, ""):
                constraints.append(f"value <= {p['max_value']}")
        else:
            unmapped.append(f"kolom {col.get('column')}: {code}")

    return constraints, unmapped


def _dataset_hooks(meta_quality: list) -> tuple[list[dict], list[str]]:
    """(hooks post[], daftar rule unmapped) dari metadata.quality[]."""
    hooks: list[dict] = []
    unmapped: list[str] = []

    for q in meta_quality or []:
        code = q.get("code")
        p = _params(q)
        if code == "row_count_range_check":
            exprs = []
            if p.get("min_rows") not in (None, ""):
                exprs.append(f"run.total_rows >= {p['min_rows']}")
            if p.get("max_rows") not in (None, ""):
                exprs.append(f"run.total_rows <= {p['max_rows']}")
            if exprs:
                hooks.append({"type": "check", "check": " and ".join(exprs),
                              "on_failure": _on_failure(q)})
        elif code == "freshness_check":
            hours = None
            try:
                hours = int(p.get("max_age")) * _AGE_UNIT_HOURS.get(p.get("age_unit"), 1)
            except (TypeError, ValueError):
                pass
            ts_col = p.get("timestamp_column") or "updated_at"
            if hours:
                hooks.append({
                    # Ekspresi freshness bergantung engine — sesuaikan di sisi Sling.
                    "type": "check",
                    "check": f"run.freshness_hours({ts_col}) <= {hours}",
                    "on_failure": _on_failure(q),
                })
        elif code == "custom_sql_check":
            if p.get("query"):
                query = str(p["query"])
                if p.get("expectation"):
                    query += f"  -- diharapkan: {p['expectation']}"
                hooks.append({"type": "query", "query": query})
        else:
            unmapped.append(f"dataset: {code}")

    return hooks, unmapped


def beescout_to_sling(contract: dict) -> str:
    """Konversi satu kontrak BeeScout (dict) → string YAML konfigurasi Sling."""
    meta = contract.get("metadata") or {}
    columns: dict[str, str] = {}
    unmapped: list[str] = []

    for col in (contract.get("model") or []):
        name = col.get("column")
        if not name:
            continue
        col_type = str(col.get("logical_type") or "string").lower()
        constraints, col_unmapped = _column_constraints(col)
        unmapped.extend(col_unmapped)
        columns[name] = f"{col_type} | {' and '.join(constraints)}" if constraints else col_type

    hooks, ds_unmapped = _dataset_hooks(meta.get("quality"))
    unmapped.extend(ds_unmapped)

    doc: dict = {"columns": columns}
    if hooks:
        doc["hooks"] = {"post": hooks}

    header = (
        "# Konfigurasi kualitas data Sling — di-export dari BeeScout\n"
        f"# Kontrak: {contract.get('contract_number', '-')} — {meta.get('name', '-')}\n"
        "# Catatan:\n"
        "#   - source/target koneksi bukan bagian kontrak — lengkapi sendiri.\n"
        "#   - on_failure hook: dari field on_failure rule bila ada (#151);\n"
        "#     fallback severity (high -> abort, selainnya warn).\n"
        "#   - Ekspresi freshness/row-count bisa perlu penyesuaian versi engine.\n"
        "# Pemetaan: data-contract/docs/quality-rules.md + docs/converters.md\n"
    )
    body = yaml.safe_dump(doc, sort_keys=False, allow_unicode=True,
                          default_flow_style=False)

    footer = ""
    if unmapped:
        footer = (
            "\n# UNMAPPED — rule tanpa padanan Sling (tidak di-drop diam-diam,\n"
            "# tangani manual atau lewat engine lain):\n"
            + "".join(f"#   - {u}\n" for u in unmapped)
        )

    return header + body + footer


# ─── Registrasi add-on (#154) ────────────────────────────────────────────────

from app.addons.converters.base import Converter

CONVERTER = Converter(
    format_id="sling",
    label="Sling YAML (data quality)",
    file_extension="sling.yaml",
    media_type="application/yaml",
    export_fn=beescout_to_sling,
    import_fn=None,   # export-only — Sling config bukan sumber kontrak
)
