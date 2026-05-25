"""
Tests untuk pengajuan modul rule catalog dari user/developer (issue #69).

Flow yang diuji:
- Admin/root submit modul → langsung tersimpan ke katalog (perilaku lama).
- User/developer submit modul → masuk approvals (type=rule_catalog_create),
  TIDAK langsung tersimpan.
- Code yang sudah ada di katalog → 409 di submit.
- Pengajuan duplikat (code yang sama masih pending) → 409.
- Tidak ada admin/root aktif → 503 (operasional, bukan blocker hard).
- Vote pada approval rule_catalog_create:
  - Approve sampai konsensus → modul masuk ke catalog_rules.
  - Approve sampai konsensus tapi code keburu dipakai admin → reject otomatis.
  - Reject → tidak ada side-effect ke catalog/contract.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock


def _make_cursor(items):
    cursor = MagicMock()
    cursor.to_list = AsyncMock(return_value=items)
    return cursor


VALID_RULE = {
    "code":              "min_length",
    "label":             "Panjang Minimum",
    "description":       "Validasi panjang minimum field",
    "layer":             "column",
    "dimension":         "validity",
    "sentence_template": "Pastikan {column} minimal {n} karakter",
    "params": [
        {"key": "n", "label": "Karakter minimum", "type": "number", "required": True},
    ],
}


@pytest.fixture
def auth_as(client):
    from app.main import app
    from app.core.verificator import token_verification, access_verification

    def _setup(username: str, lvl: str = "user"):
        async def fake_user():
            return {"usr": username, "lvl": lvl, "sts": True}
        async def fake_access(*args, **kwargs):
            return None
        app.dependency_overrides[token_verification] = fake_user
        app.dependency_overrides[access_verification] = fake_access

    yield _setup
    app.dependency_overrides.clear()


# ─── Patched catalog collection ─────────────────────────────────────────────
# Conftest tidak memock `catalogcollection`. Tambah patch per-test.

@pytest.fixture
def catalog_mock(client):
    """Patch app.main.catalogcollection dengan AsyncMock."""
    from unittest.mock import patch
    cat = AsyncMock()
    with patch("app.main.catalogcollection", cat):
        yield cat


# ─── Submit /catalog/rules ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_admin_submit_rule_inserts_directly(client, auth_as, catalog_mock):
    auth_as("retno", lvl="admin")
    ac, mocks = client

    catalog_mock.find_one.side_effect = [
        None,            # first: code uniqueness check → tidak ada
        {**VALID_RULE, "is_builtin": False, "is_active": True},  # second: fetch created
    ]
    catalog_mock.insert_one = AsyncMock()

    resp = await ac.post("/catalog/rules", json=VALID_RULE)
    assert resp.status_code == 201
    body = resp.json()
    assert body["code"] == "min_length"

    catalog_mock.insert_one.assert_awaited_once()
    # Tidak ada approval doc yang dibuat
    mocks["apr"].insert_one.assert_not_called()


@pytest.mark.asyncio
async def test_user_submit_rule_creates_approval(client, auth_as, catalog_mock):
    auth_as("indah", lvl="user")
    ac, mocks = client

    catalog_mock.find_one = AsyncMock(return_value=None)        # code belum ada
    catalog_mock.insert_one = AsyncMock()
    mocks["apr"].find_one = AsyncMock(return_value=None)        # tidak ada pengajuan pending duplikat
    mocks["usr"].find = MagicMock(return_value=_make_cursor(    # steward list
        [{"username": "retno"}, {"username": "bambang"}]
    ))
    mocks["apr"].insert_one = AsyncMock()

    resp = await ac.post("/catalog/rules", json=VALID_RULE)
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "pending"
    assert body["rule_code"] == "min_length"
    assert set(body["approvers"]) == {"retno", "bambang"}

    # Modul TIDAK tersimpan ke katalog
    catalog_mock.insert_one.assert_not_called()

    # Approval doc tersimpan dengan type & target_id yang benar
    mocks["apr"].insert_one.assert_awaited_once()
    apr_doc = mocks["apr"].insert_one.await_args.args[0]
    assert apr_doc["type"] == "rule_catalog_create"
    assert apr_doc["target_id"] == "min_length"
    assert apr_doc["status"] == "pending"
    assert apr_doc["approvers_by_role"] == {"steward": ["bambang", "retno"]}


@pytest.mark.asyncio
async def test_submit_returns_409_when_code_exists(client, auth_as, catalog_mock):
    auth_as("indah", lvl="user")
    ac, _ = client

    catalog_mock.find_one = AsyncMock(return_value={"code": "min_length"})

    resp = await ac.post("/catalog/rules", json=VALID_RULE)
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_user_submit_409_when_duplicate_pending(client, auth_as, catalog_mock):
    auth_as("indah", lvl="user")
    ac, mocks = client

    catalog_mock.find_one = AsyncMock(return_value=None)
    mocks["apr"].find_one = AsyncMock(return_value={
        "approval_id": "EXIST",
        "type": "rule_catalog_create",
        "target_id": "min_length",
        "status": "pending",
    })

    resp = await ac.post("/catalog/rules", json=VALID_RULE)
    assert resp.status_code == 409
    assert "menunggu persetujuan" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_user_submit_503_when_no_steward(client, auth_as, catalog_mock):
    auth_as("indah", lvl="user")
    ac, mocks = client

    catalog_mock.find_one = AsyncMock(return_value=None)
    mocks["apr"].find_one = AsyncMock(return_value=None)
    mocks["usr"].find = MagicMock(return_value=_make_cursor([]))   # tidak ada admin aktif

    resp = await ac.post("/catalog/rules", json=VALID_RULE)
    assert resp.status_code == 503


# ─── Vote pada approval rule_catalog_create ─────────────────────────────────

@pytest.mark.asyncio
async def test_vote_applies_rule_to_catalog_on_consensus(client, auth_as, catalog_mock):
    auth_as("retno", lvl="admin")
    ac, mocks = client

    rule_doc = {**VALID_RULE, "is_builtin": False, "is_active": True}
    existing_apr = {
        "approval_id": "APR_RULE_1",
        "type": "rule_catalog_create",
        "target_id": "min_length",
        "status": "pending",
        "approvers": ["retno"],
        "approvers_by_role": {"steward": ["retno"]},
        "votes": [],
        "proposed_changes": rule_doc,
    }
    updated_apr = {**existing_apr, "votes": [{"username": "retno", "vote": "approved"}]}
    mocks["apr"].find_one = AsyncMock(side_effect=[existing_apr, updated_apr])
    mocks["apr"].update_one = AsyncMock()
    catalog_mock.find_one = AsyncMock(return_value=None)        # belum ada code di katalog
    catalog_mock.insert_one = AsyncMock()

    resp = await ac.post("/approval/APR_RULE_1/vote", json={"vote": "approved"})
    assert resp.status_code == 200
    assert "min_length" in resp.json()["message"]

    catalog_mock.insert_one.assert_awaited_once_with(rule_doc)
    # Tidak ada update ke dccollection
    mocks["dgr"].update_one.assert_not_called()


@pytest.mark.asyncio
async def test_vote_auto_rejects_when_code_taken_at_apply_time(client, auth_as, catalog_mock):
    """Race condition: setelah pengajuan dibuat, admin sempat insert manual.
    Saat steward menyetujui, kode keburu dipakai → tolak otomatis, status
    di-set rejected supaya tidak nyangkut pending."""
    auth_as("retno", lvl="admin")
    ac, mocks = client

    rule_doc = {**VALID_RULE, "is_builtin": False, "is_active": True}
    existing_apr = {
        "approval_id": "APR_RULE_2",
        "type": "rule_catalog_create",
        "target_id": "min_length",
        "status": "pending",
        "approvers": ["retno"],
        "approvers_by_role": {"steward": ["retno"]},
        "votes": [],
        "proposed_changes": rule_doc,
    }
    updated_apr = {**existing_apr, "votes": [{"username": "retno", "vote": "approved"}]}
    mocks["apr"].find_one = AsyncMock(side_effect=[existing_apr, updated_apr])
    mocks["apr"].update_one = AsyncMock()
    catalog_mock.find_one = AsyncMock(return_value={"code": "min_length"})  # admin keburu insert
    catalog_mock.insert_one = AsyncMock()

    resp = await ac.post("/approval/APR_RULE_2/vote", json={"vote": "approved"})
    assert resp.status_code == 409
    catalog_mock.insert_one.assert_not_called()


@pytest.mark.asyncio
async def test_vote_rejected_on_catalog_proposal_no_side_effect(client, auth_as, catalog_mock):
    auth_as("retno", lvl="admin")
    ac, mocks = client

    existing_apr = {
        "approval_id": "APR_RULE_3",
        "type": "rule_catalog_create",
        "target_id": "min_length",
        "status": "pending",
        "approvers": ["retno"],
        "approvers_by_role": {"steward": ["retno"]},
        "votes": [],
        "proposed_changes": VALID_RULE,
    }
    mocks["apr"].find_one = AsyncMock(return_value=existing_apr)
    mocks["apr"].update_one = AsyncMock()
    catalog_mock.insert_one = AsyncMock()

    resp = await ac.post("/approval/APR_RULE_3/vote",
                          json={"vote": "rejected", "reason": "belum perlu"})
    assert resp.status_code == 200
    assert "ditolak" in resp.json()["message"]
    catalog_mock.insert_one.assert_not_called()
    # Tidak ada update ke dccollection — bukan perubahan kontrak.
    mocks["dgr"].update_one.assert_not_called()
