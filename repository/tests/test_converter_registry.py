"""
Tests untuk converter framework (#154): registry auto-discovery + endpoint
GET /converters + generalisasi `format=` di export/validate/import.

Perilaku ODCS sendiri sudah dicover test_odcs_converter.py — di sini hanya
kontrak framework-nya.
"""

import io

import pytest
from unittest.mock import AsyncMock

from app.addons.converters import registry
from app.addons.converters.base import Converter


# ─── Registry ────────────────────────────────────────────────────────────────


def test_registry_discovers_odcs():
    conv = registry.get_converter("odcs")
    assert isinstance(conv, Converter)
    assert conv.can_export and conv.can_import
    assert conv.file_extension == "odcs.yaml"


def test_registry_unknown_format_returns_none():
    assert registry.get_converter("format-ngawur") is None


def test_available_formats_sorted_and_nonempty():
    formats = registry.available_formats()
    assert "odcs" in formats
    assert formats == sorted(formats)


# ─── Endpoints ───────────────────────────────────────────────────────────────


@pytest.fixture
def auth_any(client):
    from app.main import app
    from app.core.verificator import token_verification, access_verification

    async def fake_user():
        return {"usr": "dimas", "lvl": "developer", "sts": True,
                "tim": "platform", "cln": "c1", "typ": "user"}

    async def fake_access(*args, **kwargs):
        return None

    app.dependency_overrides[token_verification] = fake_user
    app.dependency_overrides[access_verification] = fake_access
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def admin_bypass(client):
    from app.main import app, require_admin

    async def fake_admin():
        return {"usr": "admin", "lvl": "admin", "sts": True}

    app.dependency_overrides[require_admin] = fake_admin
    yield
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_converters_endpoint(client, auth_any):
    ac, _ = client
    res = await ac.get("/converters")
    assert res.status_code == 200, res.text
    body = res.json()
    odcs = next(c for c in body if c["format_id"] == "odcs")
    assert odcs["can_export"] is True
    assert odcs["can_import"] is True
    assert set(odcs.keys()) == {"format_id", "label", "file_extension",
                                "can_export", "can_import"}


@pytest.mark.asyncio
async def test_export_unknown_format_400_lists_available(client, auth_any):
    from app.main import app
    from app.core.verificator import access_verification_filter

    async def fake_filter(*args, **kwargs):
        return None

    app.dependency_overrides[access_verification_filter] = fake_filter
    ac, _ = client
    res = await ac.get("/datacontract/CN-1/export", params={"format": "ngawur"})
    assert res.status_code == 400
    assert "odcs" in res.json()["detail"]


@pytest.mark.asyncio
async def test_validate_yaml_unknown_format_400(client, admin_bypass):
    ac, _ = client
    res = await ac.post(
        "/contracts/validate-yaml",
        params={"format": "ngawur"},
        files={"file": ("t.yaml", io.BytesIO(b"a: 1"), "text/yaml")},
    )
    assert res.status_code == 400
    assert "beescout" in res.json()["detail"]


@pytest.mark.asyncio
async def test_import_yaml_unknown_format_400(client, admin_bypass):
    ac, _ = client
    res = await ac.post(
        "/contracts/import-yaml",
        params={"format": "ngawur"},
        files={"file": ("t.yaml", io.BytesIO(b"a: 1"), "text/yaml")},
    )
    assert res.status_code == 400
    assert "beescout" in res.json()["detail"]
