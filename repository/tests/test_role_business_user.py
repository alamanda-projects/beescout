"""
Tests untuk #91 (PR-B dari #75): hapus alias role `user` → `business_user`.

Yang diuji:
- `grplvlall` tidak lagi memuat `user` — token lama beralias `user`
  ditolak access check.
- /user/create menolak group_access="user" (422 + pesan migrasi).
- PATCH /user/{username} menolak group_access="user" (422).
- scripts/rename_role_user_to_business_user.py: dry-run tidak menulis,
  apply update_many selektif ke group_access, idempoten saat tidak ada
  alias lama.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from scripts import rename_role_user_to_business_user as mig


# ── grplvlall ────────────────────────────────────────────────────────────────


def test_grplvlall_no_longer_contains_user_alias():
    from app.core.verificator import grplvlall
    assert "user" not in grplvlall
    assert "business_user" in grplvlall


# ── /user/create & PATCH /user/{username} ────────────────────────────────────


@pytest.fixture
def override_root(client):
    from app.main import app, require_root
    from app.core.verificator import token_verification, access_verification

    async def fake_root():
        return {"usr": "root", "lvl": "root", "sts": True}

    async def fake_access(*args, **kwargs):
        return None

    app.dependency_overrides[require_root] = fake_root
    app.dependency_overrides[token_verification] = fake_root
    app.dependency_overrides[access_verification] = fake_access
    yield
    app.dependency_overrides.clear()


VALID_USER = {
    "username": "indah",
    "name": "Mbak Indah",
    "password": "Str0ng!Pass",
    "group_access": "user",   # alias legacy — harus ditolak
    "data_domain": "penjualan",
    "is_active": True,
}


@pytest.mark.asyncio
async def test_user_create_rejects_legacy_user_role(client, override_root):
    ac, mocks = client
    mocks["usr"].find_one.return_value = None
    res = await ac.post("/user/create", json=VALID_USER)
    assert res.status_code == 422
    assert "business_user" in res.json()["detail"]
    mocks["usr"].insert_one.assert_not_called()


@pytest.mark.asyncio
async def test_user_update_rejects_legacy_user_role(client, override_root):
    ac, mocks = client
    mocks["usr"].find_one.return_value = {
        "username": "indah", "group_access": "business_user", "type": "user",
    }
    res = await ac.patch("/user/indah", json={"group_access": "user"})
    assert res.status_code == 422
    assert "business_user" in res.json()["detail"]
    mocks["usr"].update_one.assert_not_called()


@pytest.mark.asyncio
async def test_user_update_accepts_business_user_role(client, override_root):
    ac, mocks = client
    mocks["usr"].find_one.return_value = {
        "username": "dimas", "group_access": "developer", "type": "user",
    }
    mocks["usr"].update_one = AsyncMock()
    res = await ac.patch("/user/dimas", json={"group_access": "business_user"})
    assert res.status_code == 200, res.text
    mocks["usr"].update_one.assert_awaited_once()


# ── Migration script ─────────────────────────────────────────────────────────


def _cursor(docs):
    cur = MagicMock()
    cur.to_list = AsyncMock(return_value=list(docs))
    return cur


def _patch_usr(legacy_users: list, legacy_count: int, new_count: int):
    usr = AsyncMock()
    usr.count_documents = AsyncMock(side_effect=[legacy_count, new_count,
                                                 0, new_count + legacy_count])
    usr.find = MagicMock(return_value=_cursor(legacy_users))
    result = MagicMock()
    result.modified_count = legacy_count
    usr.update_many = AsyncMock(return_value=result)
    return patch.object(mig, "usrcollection", usr), usr


@pytest.mark.asyncio
async def test_migration_noop_when_no_legacy_users(capsys):
    cm, usr = _patch_usr([], legacy_count=0, new_count=3)
    with cm:
        rc = await mig.main(apply=True)
    assert rc == 0
    usr.update_many.assert_not_called()
    assert "Tidak ada user beralias lama" in capsys.readouterr().out


@pytest.mark.asyncio
async def test_migration_dry_run_no_write(capsys):
    users = [{"username": "indah", "name": "Mbak Indah"}]
    cm, usr = _patch_usr(users, legacy_count=1, new_count=0)
    with cm:
        rc = await mig.main(apply=False)
    assert rc == 0
    usr.update_many.assert_not_called()
    out = capsys.readouterr().out
    assert "dry-run" in out and "indah" in out


@pytest.mark.asyncio
async def test_migration_apply_updates_group_access_only():
    users = [{"username": "indah", "name": "Mbak Indah"}]
    cm, usr = _patch_usr(users, legacy_count=1, new_count=0)
    with cm:
        rc = await mig.main(apply=True)
    assert rc == 0
    usr.update_many.assert_awaited_once_with(
        {"group_access": "user"},
        {"$set": {"group_access": "business_user"}},
    )
