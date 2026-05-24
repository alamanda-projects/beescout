"""
Tests untuk approval workflow multi-peran (ADR-0005, supersedes ADR-0004 / Issue #27).

Cakupan:
- `is_consensus_reached()` — pure function role-agnostic (cocok untuk owner/
  producer/consumer dan juga approval lama dengan kunci steward).
- `derive_approvers_by_role()` — semua peran (owner+producer+consumer) dari
  metadata.stakeholders[role,username], filter user aktif.
- `vote_approval` endpoint — konsensus role-aware untuk format baru,
  fallback unanimous-count untuk approval pre-ADR-0004 (tanpa
  `approvers_by_role`), dan tetap kompatibel dengan approval ADR-0004
  in-flight (kunci `steward`).
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock


# ─── Pure function: is_consensus_reached ──────────────────────────────────────

def test_consensus_all_roles_approved():
    from app.main import is_consensus_reached
    approvers = {"owner": ["bambang"], "producer": ["dimas"], "consumer": ["indah"]}
    votes = [
        {"username": "bambang", "vote": "approved"},
        {"username": "dimas",   "vote": "approved"},
        {"username": "indah",   "vote": "approved"},
    ]
    assert is_consensus_reached(approvers, votes) is True


def test_consensus_pending_when_role_missing_vote():
    from app.main import is_consensus_reached
    approvers = {"owner": ["bambang"], "producer": ["dimas"], "consumer": ["indah"]}
    votes = [
        {"username": "bambang", "vote": "approved"},
        {"username": "dimas",   "vote": "approved"},
        # indah belum vote
    ]
    assert is_consensus_reached(approvers, votes) is False


def test_consensus_empty_role_auto_passes():
    from app.main import is_consensus_reached
    # consumer kosong → tidak perlu vote dari peran itu
    approvers = {"owner": ["bambang"], "producer": ["dimas"], "consumer": []}
    votes = [
        {"username": "bambang", "vote": "approved"},
        {"username": "dimas",   "vote": "approved"},
    ]
    assert is_consensus_reached(approvers, votes) is True


def test_consensus_quorum_one_per_role():
    from app.main import is_consensus_reached
    # 2 producer, hanya 1 yang approved → cukup
    approvers = {"owner": ["bambang"], "producer": ["dimas", "budi"], "consumer": ["indah"]}
    votes = [
        {"username": "bambang", "vote": "approved"},
        {"username": "dimas",   "vote": "approved"},
        {"username": "indah",   "vote": "approved"},
    ]
    assert is_consensus_reached(approvers, votes) is True


def test_consensus_rejected_vote_doesnt_count_as_approved():
    from app.main import is_consensus_reached
    approvers = {"owner": ["bambang"], "producer": ["dimas"], "consumer": ["indah"]}
    votes = [
        {"username": "bambang", "vote": "approved"},
        {"username": "dimas",   "vote": "rejected"},   # bukan approved
        {"username": "indah",   "vote": "approved"},
    ]
    assert is_consensus_reached(approvers, votes) is False


def test_consensus_role_agnostic_works_with_legacy_steward_key():
    """is_consensus_reached iterasi kunci apa pun — kompatibel dengan doc lama."""
    from app.main import is_consensus_reached
    legacy = {"steward": ["retno"], "producer": ["dimas"], "consumer": ["indah"]}
    votes = [
        {"username": "retno", "vote": "approved"},
        {"username": "dimas", "vote": "approved"},
        {"username": "indah", "vote": "approved"},
    ]
    assert is_consensus_reached(legacy, votes) is True


# ─── derive_approvers_by_role ─────────────────────────────────────────────────

def _make_cursor(items):
    cursor = MagicMock()
    cursor.to_list = AsyncMock(return_value=items)
    return cursor


@pytest.mark.asyncio
async def test_derive_owner_producer_consumer_all_from_stakeholders(client):
    from app.main import derive_approvers_by_role
    _, mocks = client

    # Hanya satu query: validasi user aktif (semua peran sekarang dari stakeholders).
    mocks["usr"].find = MagicMock(return_value=_make_cursor(
        [{"username": "bambang"}, {"username": "dimas"}, {"username": "indah"}]
    ))

    contract = {"metadata": {"stakeholders": [
        {"name": "Pak Bambang", "role": "owner",    "username": "bambang"},
        {"name": "Mas Dimas",   "role": "producer", "username": "dimas"},
        {"name": "Mbak Indah",  "role": "consumer", "username": "indah"},
    ]}}
    approvers, fallback = await derive_approvers_by_role(contract)
    assert approvers == {
        "owner":    ["bambang"],
        "producer": ["dimas"],
        "consumer": ["indah"],
    }
    assert fallback == []


@pytest.mark.asyncio
async def test_derive_marks_empty_roles_as_fallback(client):
    from app.main import derive_approvers_by_role
    _, mocks = client

    # Tidak ada stakeholder ber-username → query validasi user tidak terpanggil
    # (kandidat kosong). Tapi MagicMock memberi default return value.
    mocks["usr"].find = MagicMock(return_value=_make_cursor([]))

    contract = {"metadata": {"stakeholders": [
        {"name": "Pak Bambang", "role": "owner"},     # tanpa username → skip
        {"name": "Mas Dimas",   "role": "producer"},  # tanpa username → skip
    ]}}
    approvers, fallback = await derive_approvers_by_role(contract)
    assert approvers == {"owner": [], "producer": [], "consumer": []}
    assert sorted(fallback) == ["consumer", "owner", "producer"]


@pytest.mark.asyncio
async def test_derive_skips_inactive_stakeholder_users(client):
    from app.main import derive_approvers_by_role
    _, mocks = client

    # 'budi' tidak dikembalikan oleh query → dianggap inaktif & di-skip.
    mocks["usr"].find = MagicMock(return_value=_make_cursor(
        [{"username": "dimas"}, {"username": "bambang"}]
    ))

    contract = {"metadata": {"stakeholders": [
        {"name": "Pak Bambang", "role": "owner",    "username": "bambang"},
        {"name": "Mas Dimas",   "role": "producer", "username": "dimas"},
        {"name": "Pak Budi",    "role": "producer", "username": "budi"},
    ]}}
    approvers, fallback = await derive_approvers_by_role(contract)
    assert approvers["owner"]    == ["bambang"]
    assert approvers["producer"] == ["dimas"]   # budi inaktif → tidak masuk
    assert "consumer" in fallback


@pytest.mark.asyncio
async def test_derive_ignores_non_approver_stakeholder_roles(client):
    """Stakeholder dengan peran non-approver (engineer/analyst/dll) tidak masuk."""
    from app.main import derive_approvers_by_role
    _, mocks = client

    mocks["usr"].find = MagicMock(return_value=_make_cursor([{"username": "bambang"}]))

    contract = {"metadata": {"stakeholders": [
        {"name": "Pak Bambang", "role": "owner",    "username": "bambang"},
        {"name": "Mas Engineer","role": "engineer", "username": "eng"},
        {"name": "Mbak Analyst","role": "analyst",  "username": "ana"},
        {"name": "Mas Steward", "role": "steward",  "username": "stw"},  # bukan auto-approver
    ]}}
    approvers, fallback = await derive_approvers_by_role(contract)
    assert approvers == {"owner": ["bambang"], "producer": [], "consumer": []}
    assert sorted(fallback) == ["consumer", "producer"]


# ─── /approval/{id}/vote endpoint ────────────────────────────────────────────

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
    """ADR-0005: setelah vote terakhir per peran (owner+producer+consumer), apply."""
    auth_as("indah", lvl="user")
    ac, mocks = client

    existing_record = {
        "approval_id": "APR1",
        "contract_number": "CN1",
        "status": "pending",
        "approvers": ["bambang", "dimas", "indah"],
        "approvers_by_role": {
            "owner": ["bambang"], "producer": ["dimas"], "consumer": ["indah"],
        },
        "votes": [
            {"username": "bambang", "vote": "approved"},
            {"username": "dimas",   "vote": "approved"},
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

    # update_one dipanggil: push vote (1) + set status approved (1) di apr;
    # apply ke kontrak (1) di dgr.
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
        "approvers": ["bambang", "dimas", "indah"],
        "approvers_by_role": {
            "owner": ["bambang"], "producer": ["dimas"], "consumer": ["indah"],
        },
        "votes": [{"username": "bambang", "vote": "approved"}],
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
async def test_vote_compat_with_adr_0004_steward_key(client, auth_as):
    """Approval in-flight format ADR-0004 (kunci `steward`) tetap bisa diselesaikan."""
    auth_as("indah", lvl="user")
    ac, mocks = client

    existing = {
        "approval_id": "APR_0004",
        "contract_number": "CN_OLD4",
        "status": "pending",
        "approvers": ["retno", "dimas", "indah"],
        "approvers_by_role": {
            "steward": ["retno"], "producer": ["dimas"], "consumer": ["indah"],
        },
        "votes": [
            {"username": "retno", "vote": "approved"},
            {"username": "dimas", "vote": "approved"},
        ],
        "proposed_changes": {"metadata": {"name": "Updated legacy"}},
    }
    updated = {**existing, "votes": existing["votes"] + [{"username": "indah", "vote": "approved"}]}
    mocks["apr"].find_one = AsyncMock(side_effect=[existing, updated])
    mocks["apr"].update_one = AsyncMock()
    mocks["dgr"].update_one = AsyncMock()

    resp = await ac.post("/approval/APR_0004/vote", json={"vote": "approved"})
    assert resp.status_code == 200
    assert "berhasil diterapkan" in resp.json()["message"]
    mocks["dgr"].update_one.assert_awaited_once()


@pytest.mark.asyncio
async def test_vote_backward_compat_old_record_without_approvers_by_role(client, auth_as):
    """Approval pre-ADR-0004 tanpa approvers_by_role → fallback unanimous-count."""
    auth_as("bambang", lvl="admin")
    ac, mocks = client

    existing = {
        "approval_id": "APR_OLD",
        "contract_number": "CN_OLD",
        "status": "pending",
        "approvers": ["retno", "bambang"],
        "votes": [{"username": "retno", "vote": "approved"}],
        "proposed_changes": {"metadata": {"name": "Legacy"}},
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
        "approvers": ["bambang", "dimas", "indah"],
        "approvers_by_role": {
            "owner": ["bambang"], "producer": ["dimas"], "consumer": ["indah"],
        },
        "votes": [{"username": "bambang", "vote": "approved"}],
        "proposed_changes": {},
    }
    mocks["apr"].find_one = AsyncMock(return_value=existing)
    mocks["apr"].update_one = AsyncMock()
    mocks["dgr"].update_one = AsyncMock()

    resp = await ac.post("/approval/APR3/vote", json={"vote": "rejected", "reason": "data salah"})
    assert resp.status_code == 200
    assert "ditolak" in resp.json()["message"]
    assert mocks["apr"].update_one.await_count == 2
    assert mocks["dgr"].update_one.await_count == 1
