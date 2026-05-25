"""
Tests untuk break-glass recovery script (scripts/recover_root.py, issue #61).

Tidak butuh MongoDB — koleksi di-mock di level objek, sama seperti test lain.
"""

import argparse
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from scripts import recover_root


# ── Async iterator helper untuk meniru usrcollection.find() ───────────────────

class _AsyncCursor:
    def __init__(self, docs):
        self._docs = list(docs)

    def __aiter__(self):
        return self

    async def __anext__(self):
        if not self._docs:
            raise StopAsyncIteration
        return self._docs.pop(0)


def _make_collection(find_one_result, find_results):
    col = AsyncMock()
    col.find_one.return_value = find_one_result
    col.find = MagicMock(return_value=_AsyncCursor(find_results))
    col.update_many.return_value = MagicMock(modified_count=len(find_results))
    return col


def _args(**overrides):
    base = dict(username="root", name="Root User", data_domain="platform",
                password="Str0ng!Pass", apply=False)
    base.update(overrides)
    return argparse.Namespace(**base)


# ── validate_password ─────────────────────────────────────────────────────────

@pytest.mark.parametrize("pwd", ["short1!", "alllower1!", "ALLUPPER1!", "NoDigits!!", "NoSpecial1"])
def test_validate_password_rejects_weak(pwd):
    assert recover_root.validate_password(pwd) is not None


def test_validate_password_accepts_strong():
    assert recover_root.validate_password("Str0ng!Pass") is None


# ── main() — dry-run ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_dry_run_makes_no_writes():
    col = _make_collection({"username": "root", "group_access": "root"}, [])
    with patch.object(recover_root, "usrcollection", col):
        rc = await recover_root.main(_args(apply=False))
    assert rc == 0
    col.update_many.assert_not_called()
    col.update_one.assert_not_called()
    col.insert_one.assert_not_called()


# ── main() — recovery mode ────────────────────────────────────────────────────

def _mock_dom_empty():
    """Empty domain collection — _seed_default_domains() akan insert keduanya."""
    dom = AsyncMock()
    dom.find_one.return_value = None
    return dom


@pytest.mark.asyncio
async def test_recovery_resets_existing_root_and_disables_others():
    col = _make_collection(
        {"username": "root", "group_access": "root", "is_active": False},
        [{"username": "oldroot", "group_access": "root", "is_active": True}],
    )
    dom = _mock_dom_empty()
    with patch.object(recover_root, "usrcollection", col), \
         patch.object(recover_root, "domcollection", dom):
        rc = await recover_root.main(_args(username="root", apply=True))
    assert rc == 0
    # root lain di-non-aktifkan
    col.update_many.assert_called_once()
    query, update = col.update_many.call_args.args
    assert query["group_access"] == "root"
    assert query["username"] == {"$ne": "root"}
    assert update == {"$set": {"is_active": False}}
    # akun root yang ada di-reset & diaktifkan, dan data_domain dinormalkan ke 'root' (#74)
    col.update_one.assert_called_once()
    _, upd = col.update_one.call_args.args
    assert upd["$set"]["is_active"] is True
    assert upd["$set"]["group_access"] == "root"
    assert upd["$set"]["data_domain"] == "root"
    assert "recovered_at" in upd["$set"]
    col.insert_one.assert_not_called()


# ── main() — create mode ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_mode_inserts_new_active_root():
    col = _make_collection(None, [{"username": "oldroot", "group_access": "root"}])
    dom = _mock_dom_empty()
    with patch.object(recover_root, "usrcollection", col), \
         patch.object(recover_root, "domcollection", dom):
        rc = await recover_root.main(_args(username="newroot", apply=True))
    assert rc == 0
    col.insert_one.assert_called_once()
    doc = col.insert_one.call_args.args[0]
    assert doc["username"] == "newroot"
    assert doc["group_access"] == "root"
    assert doc["is_active"] is True
    # #74: data_domain root account selalu 'root', --data-domain diabaikan
    assert doc["data_domain"] == "root"
    col.update_many.assert_called_once()  # root lama di-non-aktifkan


@pytest.mark.asyncio
async def test_apply_seeds_default_domains(tmp_path):
    """Setelah recovery/create, domain 'root' & 'admin' di-seed bila belum ada (#74)."""
    col = _make_collection(None, [])
    dom = _mock_dom_empty()
    with patch.object(recover_root, "usrcollection", col), \
         patch.object(recover_root, "domcollection", dom):
        rc = await recover_root.main(_args(username="newroot", apply=True))
    assert rc == 0
    inserted = [c.args[0]["name"] for c in dom.insert_one.call_args_list]
    assert set(inserted) == {"root", "admin"}
    for c in dom.insert_one.call_args_list:
        assert c.args[0]["is_default"] is True


@pytest.mark.asyncio
async def test_create_mode_requires_name():
    col = _make_collection(None, [])
    with patch.object(recover_root, "usrcollection", col):
        rc = await recover_root.main(_args(username="newroot", name=None, apply=True))
    assert rc == 1
    col.insert_one.assert_not_called()


@pytest.mark.asyncio
async def test_refuses_to_promote_non_root_account():
    col = _make_collection({"username": "bob", "group_access": "admin"}, [])
    with patch.object(recover_root, "usrcollection", col):
        rc = await recover_root.main(_args(username="bob", apply=True))
    assert rc == 1
    col.update_one.assert_not_called()
    col.insert_one.assert_not_called()


@pytest.mark.asyncio
async def test_rejects_weak_password_flag():
    col = _make_collection({"username": "root", "group_access": "root"}, [])
    with patch.object(recover_root, "usrcollection", col):
        rc = await recover_root.main(_args(password="weak", apply=True))
    assert rc == 1
