"""
Generate Postman Collection v2.1 dari skema OpenAPI FastAPI BeeScout (#55).

Ini menjadikan koleksi Postman selalu in-sync dengan API: source of truth
tetap `repository/app/main.py` + Pydantic models. Jalankan ulang setiap kali
ada endpoint berubah (lihat CLAUDE.md "Definition of Done").

Output:
    docs/api/beescout.postman_collection.json   (komit ke repo)

Tidak mengirim request apa pun — hanya membaca `app.openapi()`. Aman dijalankan
tanpa MongoDB (route handler tidak dipanggil).
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

# Import app via path test yang sudah ada — env vars dimuat di-load time.
from app.main import app

# Tag → display label & ringkasan singkat untuk folder Postman.
TAG_LABELS: dict[str, tuple[str, str]] = {
    "system":                ("00. System & Bootstrap",     "Health check, status setup awal, dan endpoint bootstrap root pertama."),
    "user":                  ("01. User & Service Account", "Login/logout, manajemen user (root only), direktori user, dan Service Account Key."),
    "domain":                ("02. Domain Catalog",         "Katalog domain terstandarisasi — kunci akses kontrak (`data_domain`)."),
    "datacontract":          ("03. Data Contract",          "CRUD kontrak. Hanya `datacontract/lists` & `mine` di-filter scope; selebihnya admin."),
    "datacontract_filtered": ("04. Data Contract — Filtered","View per-contract dengan validasi scope team (consumer match)."),
    "approval":              ("05. Approval Workflow",      "Antrean approval lintas peran (Owner/Producer/Consumer per ADR-0005)."),
    "catalog":               ("06. Rule Catalog",           "Katalog modul aturan kualitas reusable."),
    "contracts":             ("07. YAML Import",            "Validasi & import kontrak format YAML BeeScout standard."),
}

UNTAGGED_FOLDER = ("99. Lain-lain", "Endpoint yang tidak punya tag eksplisit.")

# Placeholder value default per JSON Schema type — supaya body contoh terisi
# sesuatu yang valid (bukan null) dan langsung bisa di-edit.
PLACEHOLDERS = {
    "string":  "string",
    "integer": 0,
    "number":  0,
    "boolean": True,
    "array":   [],
    "object":  {},
}


def deref(schema: dict[str, Any], components: dict[str, Any]) -> dict[str, Any]:
    """Resolve `$ref` 1 level (cukup untuk request body FastAPI biasa)."""
    ref = schema.get("$ref")
    if not ref:
        return schema
    # Format: "#/components/schemas/Name"
    name = ref.rsplit("/", 1)[-1]
    return components.get("schemas", {}).get(name, {})


def example_for(schema: dict[str, Any], components: dict[str, Any], _depth: int = 0) -> Any:
    """Bangun body contoh dari JSON Schema. Pakai field `example` kalau ada."""
    if _depth > 4:
        return None  # guard rekursi untuk model yang self-referencing
    schema = deref(schema, components)
    if "example" in schema:
        return schema["example"]
    t = schema.get("type")
    if t == "object" or "properties" in schema:
        out: dict[str, Any] = {}
        for prop, sub in (schema.get("properties") or {}).items():
            out[prop] = example_for(sub, components, _depth + 1)
        return out
    if t == "array":
        items = schema.get("items") or {}
        return [example_for(items, components, _depth + 1)]
    if "enum" in schema:
        return schema["enum"][0]
    return PLACEHOLDERS.get(t, None)


def build_url(path: str) -> dict[str, Any]:
    """`/user/{username}` → Postman url object dengan path params terpisah."""
    # Ganti `{name}` → `:name` untuk segmen variable Postman.
    segments = []
    variables = []
    for seg in path.strip("/").split("/"):
        if seg.startswith("{") and seg.endswith("}"):
            name = seg[1:-1]
            segments.append(f":{name}")
            variables.append({"key": name, "value": ""})
        else:
            segments.append(seg)
    url: dict[str, Any] = {
        "raw": "{{base_url}}/" + "/".join(segments),
        "host": ["{{base_url}}"],
        "path": segments,
    }
    if variables:
        url["variable"] = variables
    return url


def build_request(method: str, path: str, op: dict[str, Any], components: dict[str, Any]) -> dict[str, Any]:
    summary = op.get("summary") or f"{method.upper()} {path}"
    description = op.get("description") or ""

    request: dict[str, Any] = {
        "method": method.upper(),
        "header": [],
        "url": build_url(path),
        "description": description.strip(),
    }

    # Query params
    query_params = [
        {
            "key": p["name"],
            "value": "",
            "description": p.get("description") or "",
            "disabled": not p.get("required", False),
        }
        for p in op.get("parameters", [])
        if p.get("in") == "query"
    ]
    if query_params:
        request["url"]["query"] = query_params

    # Body
    body = op.get("requestBody")
    if body:
        content = body.get("content", {})
        # Prefer application/json; fallback multipart untuk upload YAML.
        if "application/json" in content:
            schema = content["application/json"].get("schema", {})
            example = example_for(schema, components)
            request["header"].append({"key": "Content-Type", "value": "application/json"})
            request["body"] = {
                "mode": "raw",
                "raw": json.dumps(example, indent=2, ensure_ascii=False),
                "options": {"raw": {"language": "json"}},
            }
        elif "multipart/form-data" in content:
            request["body"] = {
                "mode": "formdata",
                "formdata": [{"key": "file", "type": "file", "src": []}],
            }

    return {"name": f"{method.upper()} {path} — {summary}", "request": request, "response": []}


def main() -> int:
    schema = app.openapi()
    components = schema.get("components", {})
    paths = schema.get("paths", {})

    # Kelompokkan operations per tag (FastAPI: tag pertama).
    by_tag: dict[str, list[dict[str, Any]]] = {}
    for path, methods in paths.items():
        for method, op in methods.items():
            if method not in {"get", "post", "put", "patch", "delete"}:
                continue
            tag = (op.get("tags") or [""])[0]
            by_tag.setdefault(tag, []).append(build_request(method, path, op, components))

    # Susun folder sesuai urutan TAG_LABELS, sisanya jadi folder Lain-lain.
    items = []
    for tag, (label, desc) in TAG_LABELS.items():
        if tag in by_tag:
            items.append({"name": label, "description": desc, "item": by_tag.pop(tag)})
    for tag, ops in sorted(by_tag.items()):
        label, desc = UNTAGGED_FOLDER if not tag else (tag, "")
        items.append({"name": label, "description": desc, "item": ops})

    collection = {
        "info": {
            "name": "BeeScout API",
            "description": (
                "Auto-generated Postman Collection dari FastAPI OpenAPI schema. "
                "Jangan edit manual — jalankan `make regen-postman` setelah mengubah "
                "endpoint backend (lihat CLAUDE.md DoD). "
                "Setup awal & cara login: lihat docs/api/README.md."
            ),
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        },
        "item": items,
        "variable": [{"key": "base_url", "value": "{{base_url}}"}],
    }

    out_path = Path(os.environ.get("POSTMAN_OUT", "/work/docs/api/beescout.postman_collection.json"))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(collection, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    total = sum(len(by_tag.get(t, [])) + len(folder["item"]) for t, folder in zip([], items)) if False else sum(len(f["item"]) for f in items)
    print(f"✓ {total} requests written to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
