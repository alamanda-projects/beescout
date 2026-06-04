"""
Tests for ADR-0007 derive_team_scope helper + integration di
/datacontract/filter list mode + access_verification_filter.

Sumber kebenaran scope visibilitas: metadata.stakeholders[role IN
(consumer, producer)].username → user.data_domain.

Phase 3 (#94): fallback ke metadata.consumer[].name SUDAH DIHAPUS — migration
legacy sudah dijalankan & diverifikasi di production. Kontrak tanpa stakeholder
consumer/producer ber-username aktif → scope kosong (hanya admin/root yang
melihatnya). `metadata.consumer[]` kini murni documentary (use_case).
"""

import pytest
from unittest.mock import AsyncMock, MagicMock


def _cursor(docs):
    """Sync find() yang to_list()-nya awaitable."""
    cur = MagicMock()
    cur.to_list = AsyncMock(return_value=docs)
    return cur


def _user_payload(level: str, tim: str = "penjualan", usr: str = "user_x"):
    return {"usr": usr, "typ": "user", "lvl": level, "sts": True, "tim": tim}


@pytest.fixture
def override_token():
    from app.main import app
    from app.core.verificator import token_verification

    def _set(payload: dict):
        app.dependency_overrides[token_verification] = lambda: payload

    yield _set
    app.dependency_overrides.pop(token_verification, None)


# ── derive_team_scope (unit) ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_derive_scope_from_stakeholders(client):
    """Stakeholder ber-role consumer/producer dengan username valid →
    data_domain user-nya masuk ke scope."""
    _, mocks = client
    from app.core.verificator import derive_team_scope

    mocks["usr"].find = MagicMock(return_value=_cursor([
        {"username": "dimas", "data_domain": "penjualan"},
        {"username": "indah", "data_domain": "marketing"},
    ]))
    contract = {
        "metadata": {
            "stakeholders": [
                {"username": "dimas", "role": "consumer"},
                {"username": "indah", "role": "producer"},
                {"username": "bambang", "role": "owner"},  # owner: tidak ikut scope
            ],
            "consumer": [{"name": "harus-diabaikan"}],  # documentary — tidak pernah jadi scope
        }
    }
    scope = await derive_team_scope(contract)
    assert scope == {"penjualan", "marketing"}


@pytest.mark.asyncio
async def test_derive_scope_legacy_consumer_no_longer_visible(client):
    """Phase 3: kontrak legacy tanpa stakeholders ber-username → scope KOSONG.
    Fallback ke metadata.consumer[].name sudah dihapus (migration prod selesai)."""
    _, mocks = client
    from app.core.verificator import derive_team_scope

    mocks["usr"].find = MagicMock(return_value=_cursor([]))
    contract = {
        "metadata": {
            "stakeholders": [{"name": "Pak X", "role": "owner"}],  # no username
            "consumer": [{"name": "penjualan"}, {"name": "analytics"}],
        }
    }
    scope = await derive_team_scope(contract)
    assert scope == set()


@pytest.mark.asyncio
async def test_derive_scope_inactive_stakeholder_user_no_fallback(client):
    """Username di stakeholders ada, tapi user di DB inactive → scope KOSONG.
    Phase 3: tidak ada lagi fallback ke consumer[]."""
    _, mocks = client
    from app.core.verificator import derive_team_scope

    # find() return empty (user inactive di-filter is_active:True)
    mocks["usr"].find = MagicMock(return_value=_cursor([]))
    contract = {
        "metadata": {
            "stakeholders": [{"username": "dimas_resigned", "role": "consumer"}],
            "consumer": [{"name": "penjualan"}],
        }
    }
    scope = await derive_team_scope(contract)
    assert scope == set()


@pytest.mark.asyncio
async def test_derive_scope_empty_when_no_source(client):
    """Kontrak tanpa stakeholders & tanpa consumer[] → scope kosong."""
    _, mocks = client
    from app.core.verificator import derive_team_scope

    mocks["usr"].find = MagicMock(return_value=_cursor([]))
    contract = {"metadata": {}}
    scope = await derive_team_scope(contract)
    assert scope == set()


# ── /datacontract/filter list mode (integration) ──────────────────────────────


@pytest.mark.asyncio
async def test_filter_list_developer_sees_only_team_scope(client, override_token):
    """Developer tim 'penjualan' → hanya melihat kontrak yang scope-nya
    mengandung 'penjualan' via stakeholder. Phase 3: kontrak legacy yang hanya
    punya consumer[]='penjualan' (tanpa stakeholder ber-username) TIDAK terlihat."""
    ac, mocks = client

    # Dua kontrak: CN-1 via stakeholders (terlihat), CN-2 legacy consumer[]
    # 'penjualan' tanpa stakeholder ber-username → tidak terlihat (fallback gone).
    mocks["dgr"].find = MagicMock(return_value=_cursor([
        {
            "standard_version": "1.0",
            "contract_number": "CN-1",
            "metadata": {
                "version": "1.0", "type": "CSV", "name": "Sales", "owner": "marketing",
                "effective_date": "2024-01-01", "expiry_date": "2025-12-31",
                "stakeholders": [{"name": "Mas Dimas", "username": "dimas", "role": "consumer"}],
            },
            "model": [], "ports": [], "examples": {"type": None, "data": None},
        },
        {
            "standard_version": "1.0",
            "contract_number": "CN-2",
            "metadata": {
                "version": "1.0", "type": "CSV", "name": "Other", "owner": "x",
                "effective_date": "2024-01-01", "expiry_date": "2025-12-31",
                "consumer": [{"name": "penjualan"}],  # legacy-only → tak lagi terlihat
            },
            "model": [], "ports": [], "examples": {"type": None, "data": None},
        },
    ]))
    # Lookup stakeholder username → user
    mocks["usr"].find = MagicMock(return_value=_cursor([
        {"username": "dimas", "data_domain": "penjualan"},
    ]))

    override_token(_user_payload("developer", tim="penjualan", usr="dimas"))
    res = await ac.get("/datacontract/filter")
    assert res.status_code == 200, res.text
    body = res.json()
    assert len(body) == 1
    assert body[0]["contract_number"] == "CN-1"


@pytest.mark.asyncio
async def test_filter_list_producer_team_now_sees_contract(client, override_token):
    """Producer simetri (ADR-0007): tim user yang jadi stakeholder
    role=producer juga ter-filter — sebelumnya hanya consumer."""
    ac, mocks = client

    mocks["dgr"].find = MagicMock(return_value=_cursor([
        {
            "standard_version": "1.0",
            "contract_number": "CN-3",
            "metadata": {
                "version": "1.0", "type": "CSV", "name": "X", "owner": "y",
                "effective_date": "2024-01-01", "expiry_date": "2025-12-31",
                "stakeholders": [{"name": "Ari Producer", "username": "ari", "role": "producer"}],
            },
            "model": [], "ports": [], "examples": {"type": None, "data": None},
        },
    ]))
    mocks["usr"].find = MagicMock(return_value=_cursor([
        {"username": "ari", "data_domain": "engineering"},
    ]))

    override_token(_user_payload("developer", tim="engineering", usr="ari"))
    res = await ac.get("/datacontract/filter")
    assert res.status_code == 200, res.text
    body = res.json()
    assert len(body) == 1
    assert body[0]["contract_number"] == "CN-3"


@pytest.mark.asyncio
async def test_filter_list_no_match_returns_empty(client, override_token):
    """User yang tim-nya tidak di scope manapun → list kosong, bukan 403."""
    ac, mocks = client

    mocks["dgr"].find = MagicMock(return_value=_cursor([
        {
            "standard_version": "1.0",
            "contract_number": "CN-4",
            "metadata": {
                "version": "1.0", "type": "CSV", "name": "X", "owner": "y",
                "consumer": [{"name": "tim-lain"}],
            },
            "model": [], "ports": [], "examples": {"type": None, "data": None},
        },
    ]))
    mocks["usr"].find = MagicMock(return_value=_cursor([]))

    override_token(_user_payload("developer", tim="penjualan"))
    res = await ac.get("/datacontract/filter")
    assert res.status_code == 200
    assert res.json() == []
