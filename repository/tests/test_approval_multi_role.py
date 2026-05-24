"""
Tests untuk approval workflow multi-peran (ADR-0004 / Issue #27).

Cakupan:
- `is_consensus_reached()` — pure function, langsung diuji.
- `derive_approvers_by_role()` — mock usrcollection, periksa derivasi steward
  + producer + consumer + skip user inaktif.
- `vote_approval` endpoint — konsensus berbasis peran (semua peran approved →
  applied) dan backward compat untuk approval lama tanpa `approvers_by_role`.
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock


# ─── Pure function: is_consensus_reached ──────────────────────────────────────

def test_consensus_all_roles_approved():
    from app.main import is_consensus_reached
    approvers = {"steward": ["retno"], "producer": ["dimas"], "consumer": ["indah"]}
    votes = [
        {"username": "retno", "vote": "approved"},
        {"username": "dimas", "vote": "approved"},
        {"username": "indah", "vote": "approved"},
    ]
    assert is_consensus_reached(approvers, votes) is True


def test_consensus_pending_when_role_missing_vote():
    from app.main import is_consensus_reached
    approvers = {"steward": ["retno"], "producer": ["dimas"], "consumer": ["indah"]}
    votes = [
        {"username": "retno", "vote": "approved"},
        {"username": "dimas", "vote": "approved"},
        # indah belum vote
    ]
    assert is_consensus_reached(approvers, votes) is False


def test_consensus_empty_role_auto_passes():
    from app.main import is_consensus_reached
    # consumer kosong → tidak perlu vote dari peran itu
    approvers = {"steward": ["retno"], "producer": ["dimas"], "consumer": []}
    votes = [
        {"username": "retno", "vote": "approved"},
        {"username": "dimas", "vote": "approved"},
    ]
    assert is_consensus_reached(approvers, votes) is True


def test_consensus_quorum_one_per_role():
    from app.main import is_consensus_reached
    # 2 producer, hanya 1 yang approved → cukup
    approvers = {"steward": ["retno"], "producer": ["dimas", "budi"], "consumer": ["indah"]}
    votes = [
        {"username": "retno", "vote": "approved"},
        {"username": "dimas", "vote": "approved"},
        {"username": "indah", "vote": "approved"},
    ]
    assert is_consensus_reached(approvers, votes) is True


def test_consensus_rejected_vote_doesnt_count_as_approved():
    from app.main import is_consensus_reached
    approvers = {"steward": ["retno"], "producer": ["dimas"], "consumer": ["indah"]}
    votes = [
        {"username": "retno", "vote": "approved"},
        {"username": "dimas", "vote": "rejected"},   # bukan approved
        {"username": "indah", "vote": "approved"},
    ]
    assert is_consensus_reached(approvers, votes) is False


# ─── derive_approvers_by_role ─────────────────────────────────────────────────

def _make_cursor(items):
    cursor = MagicMock()
    cursor.to_list = AsyncMock(return_value=items)
    return cursor


@pytest.mark.asyncio
async def test_derive_steward_producer_consumer(client):
    from app.main import derive_approvers_by_role
    _, mocks = client

    # find() dipanggil 2x: pertama untuk steward, kedua untuk validasi user aktif.
    mocks["usr"].find = MagicMock(side_effect=[
        _make_cursor([{"username": "retno"}, {"username": "bambang"}]),
        _make_cursor([{"username": "dimas"}, {"username": "indah"}]),
    ])

    contract = {"metadata": {"stakeholders": [
        {"name": "Mas Dimas",  "role": "producer", "username": "dimas"},
        {"name": "Mbak Indah", "role": "consumer", "username": "indah"},
    ]}}
    approvers, fallback = await derive_approvers_by_role(contract)
    assert approvers == {
        "steward":  ["bambang", "retno"],
        "producer": ["dimas"],
        "consumer": ["indah"],
    }
    assert fallback == []


@pytest.mark.asyncio
async def test_derive_marks_role_as_fallback_when_empty(client):
    from app.main import derive_approvers_by_role
    _, mocks = client

    # Hanya steward query yang relevan; tidak ada stakeholder ber-username,
    # jadi query kedua tidak dipanggil.
    mocks["usr"].find = MagicMock(return_value=_make_cursor([{"username": "retno"}]))

    contract = {"metadata": {"stakeholders": [
        {"name": "Mas Dimas", "role": "producer"},  # tanpa username → di-skip
    ]}}
    approvers, fallback = await derive_approvers_by_role(contract)
    assert approvers == {"steward": ["retno"], "producer": [], "consumer": []}
    assert sorted(fallback) == ["consumer", "producer"]


@pytest.mark.asyncio
async def test_derive_skips_inactive_stakeholder_users(client):
    from app.main import derive_approvers_by_role
    _, mocks = client

    # Steward query, lalu validasi user aktif: 'budi' tidak dikembalikan
    # → harus di-skip karena dianggap inaktif.
    mocks["usr"].find = MagicMock(side_effect=[
        _make_cursor([{"username": "retno"}]),
        _make_cursor([{"username": "dimas"}]),     # budi inaktif → tidak ada
    ])

    contract = {"metadata": {"stakeholders": [
        {"name": "Mas Dimas", "role": "producer", "username": "dimas"},
        {"name": "Pak Budi",  "role": "producer", "username": "budi"},
    ]}}
    approvers, fallback = await derive_approvers_by_role(contract)
    assert approvers["producer"] == ["dimas"]
    assert "consumer" in fallback  # consumer memang kosong


# ─── /approval/{id}/vote endpoint — backward compat & role-aware ─────────────

@pytest.fixture
def auth_as(client):
    """Override auth dependencies — return a context manager-like helper."""
    from app.main import app
    from app.core.verificator import token_verification, access_verification

    def _setup(username: str, lvl: str = "admin"):
        async def fake_user():
            return {"usr": username, "lvl": lvl, "sts": True}
        async def fake_access(*args, **kwargs):
            return None
        app.dependency_overrides[token_verification] = fake_user
        app.dependency_overrides[access_verification] = fake_access

    yield _setup
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_vote_applies_changes_when_all_roles_approve(client, auth_as):
    """Setelah vote terakhir per peran terkumpul, perubahan ter-apply."""
    auth_as("indah", lvl="user")
    ac, mocks = client

    existing_record = {
        "approval_id": "APR1",
        "contract_number": "CN1",
        "status": "pending",
        "approvers": ["retno", "dimas", "indah"],
        "approvers_by_role": {
            "steward": ["retno"], "producer": ["dimas"], "consumer": ["indah"],
        },
        "votes": [
            {"username": "retno", "vote": "approved"},
            {"username": "dimas", "vote": "approved"},
        ],
        "proposed_changes": {"metadata": {"name": "Updated"}},
    }
    updated_record = {
        **existing_record,
        "votes": existing_record["votes"] + [{"username": "indah", "vote": "approved"}],
    }
    mocks["apr"].find_one = AsyncMock(side_effect=[existing_record, updated_record])
    mocks["apr"].update_one = AsyncMock()
    mocks["dgr"].update_one = AsyncMock()

    resp = await ac.post("/approval/APR1/vote", json={"vote": "approved"})
    assert resp.status_code == 200
    assert "berhasil diterapkan" in resp.json()["message"]

    # update_one dipanggil 3x: push vote, set status=approved, apply ke kontrak.
    assert mocks["apr"].update_one.await_count == 2
    assert mocks["dgr"].update_one.await_count == 1


@pytest.mark.asyncio
async def test_vote_still_pending_when_one_role_not_yet_voted(client, auth_as):
    auth_as("dimas", lvl="developer")
    ac, mocks = client

    existing = {
        "approval_id": "APR2",
        "contract_number": "CN2",
        "status": "pending",
        "approvers": ["retno", "dimas", "indah"],
        "approvers_by_role": {
            "steward": ["retno"], "producer": ["dimas"], "consumer": ["indah"],
        },
        "votes": [{"username": "retno", "vote": "approved"}],
        "proposed_changes": {},
    }
    updated = {**existing, "votes": existing["votes"] + [{"username": "dimas", "vote": "approved"}]}
    mocks["apr"].find_one = AsyncMock(side_effect=[existing, updated])
    mocks["apr"].update_one = AsyncMock()
    mocks["dgr"].update_one = AsyncMock()

    resp = await ac.post("/approval/APR2/vote", json={"vote": "approved"})
    assert resp.status_code == 200
    assert "Menunggu" in resp.json()["message"]
    # Hanya push vote, tidak apply.
    assert mocks["apr"].update_one.await_count == 1
    mocks["dgr"].update_one.assert_not_called()


@pytest.mark.asyncio
async def test_vote_backward_compat_old_record_without_approvers_by_role(client, auth_as):
    """Approval lama tanpa approvers_by_role → fallback ke konsensus unanimous."""
    auth_as("bambang", lvl="admin")
    ac, mocks = client

    existing = {
        "approval_id": "APR_OLD",
        "contract_number": "CN_OLD",
        "status": "pending",
        "approvers": ["retno", "bambang"],
        "votes": [{"username": "retno", "vote": "approved"}],
        "proposed_changes": {"metadata": {"name": "Legacy"}},
        # approvers_by_role tidak ada → fallback path
    }
    updated = {**existing, "votes": existing["votes"] + [{"username": "bambang", "vote": "approved"}]}
    mocks["apr"].find_one = AsyncMock(side_effect=[existing, updated])
    mocks["apr"].update_one = AsyncMock()
    mocks["dgr"].update_one = AsyncMock()

    resp = await ac.post("/approval/APR_OLD/vote", json={"vote": "approved"})
    assert resp.status_code == 200
    assert "berhasil diterapkan" in resp.json()["message"]
    mocks["dgr"].update_one.assert_awaited_once()


@pytest.mark.asyncio
async def test_vote_rejected_short_circuits(client, auth_as):
    auth_as("dimas", lvl="developer")
    ac, mocks = client

    existing = {
        "approval_id": "APR3",
        "contract_number": "CN3",
        "status": "pending",
        "approvers": ["retno", "dimas", "indah"],
        "approvers_by_role": {
            "steward": ["retno"], "producer": ["dimas"], "consumer": ["indah"],
        },
        "votes": [{"username": "retno", "vote": "approved"}],
        "proposed_changes": {},
    }
    mocks["apr"].find_one = AsyncMock(return_value=existing)
    mocks["apr"].update_one = AsyncMock()
    mocks["dgr"].update_one = AsyncMock()

    resp = await ac.post("/approval/APR3/vote", json={"vote": "rejected", "reason": "data salah"})
    assert resp.status_code == 200
    assert "ditolak" in resp.json()["message"]
    # 2 update_one: push vote, set status=rejected. Plus 1 di dgr untuk reset pending state.
    assert mocks["apr"].update_one.await_count == 2
    assert mocks["dgr"].update_one.await_count == 1
