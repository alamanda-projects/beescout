"""
Tests untuk scripts/migrate_consumer_to_stakeholders.py (ADR-0007 Phase 2, #94).

Tidak butuh MongoDB — koleksi di-mock di level modul, sama seperti test lain.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from scripts import migrate_consumer_to_stakeholders as mig


def _cursor(docs):
    """Sync find() yang to_list()-nya awaitable."""
    cur = MagicMock()
    cur.to_list = AsyncMock(return_value=list(docs))
    return cur


def _patch_collections(contracts: list, users_by_team: dict[str, list]):
    """Patch dccollection & usrcollection di modul script.

    `users_by_team` adalah dict {data_domain: [{username, name}, ...]}.
    """
    dc = AsyncMock()
    dc.find = MagicMock(return_value=_cursor(contracts))
    dc.update_one.return_value = None

    usr = AsyncMock()

    def usr_find(query, _projection=None):
        team = query.get("data_domain")
        return _cursor(users_by_team.get(team, []))

    usr.find = MagicMock(side_effect=usr_find)

    return patch.multiple(mig, dccollection=dc, usrcollection=usr), dc, usr


# ── No-op cases ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_no_contracts_returns_quietly(capsys):
    cm, dc, _ = _patch_collections([], {})
    with cm:
        rc = await mig.main(apply=False)
    assert rc == 0
    dc.update_one.assert_not_called()
    out = capsys.readouterr().out
    assert "Tidak ada kontrak" in out


@pytest.mark.asyncio
async def test_dry_run_makes_no_writes(capsys):
    contracts = [{
        "_id": "doc1",
        "contract_number": "CN-1",
        "metadata": {
            "consumer": [{"name": "penjualan"}],
            "stakeholders": [],
        },
    }]
    users_by_team = {"penjualan": [{"username": "dimas", "name": "Mas Dimas"}]}
    cm, dc, _ = _patch_collections(contracts, users_by_team)
    with cm:
        rc = await mig.main(apply=False)
    assert rc == 0
    dc.update_one.assert_not_called()
    out = capsys.readouterr().out
    assert "DRY-RUN" in out
    assert "dimas" in out  # rencana ter-print


# ── Apply mode ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_apply_appends_stakeholder_for_matching_team():
    contracts = [{
        "_id": "doc1",
        "contract_number": "CN-1",
        "metadata": {
            "consumer": [{"name": "penjualan"}],
            "stakeholders": [],
        },
    }]
    users_by_team = {"penjualan": [{"username": "dimas", "name": "Mas Dimas"}]}
    cm, dc, _ = _patch_collections(contracts, users_by_team)
    with cm:
        await mig.main(apply=True)
    dc.update_one.assert_called_once()
    _, update = dc.update_one.call_args.args
    new_stakeholders = update["$push"]["metadata.stakeholders"]["$each"]
    assert new_stakeholders == [
        {"name": "Mas Dimas", "role": "consumer", "username": "dimas"},
    ]


@pytest.mark.asyncio
async def test_apply_multiple_users_per_team():
    """Beberapa user aktif di tim yang sama → semuanya ditambahkan."""
    contracts = [{
        "_id": "doc1",
        "contract_number": "CN-1",
        "metadata": {
            "consumer": [{"name": "penjualan"}],
            "stakeholders": [],
        },
    }]
    users_by_team = {
        "penjualan": [
            {"username": "dimas", "name": "Mas Dimas"},
            {"username": "ari",   "name": "Ari"},
        ],
    }
    cm, dc, _ = _patch_collections(contracts, users_by_team)
    with cm:
        await mig.main(apply=True)
    new_stakeholders = dc.update_one.call_args.args[1]["$push"]["metadata.stakeholders"]["$each"]
    usernames = {s["username"] for s in new_stakeholders}
    assert usernames == {"dimas", "ari"}


# ── Idempotency ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_skip_when_stakeholder_already_exists():
    """Idempoten: kalau stakeholder consumer dengan username tsb sudah ada,
    tidak ditambah lagi."""
    contracts = [{
        "_id": "doc1",
        "contract_number": "CN-1",
        "metadata": {
            "consumer": [{"name": "penjualan"}],
            "stakeholders": [
                {"name": "Mas Dimas", "role": "consumer", "username": "dimas"},
            ],
        },
    }]
    users_by_team = {"penjualan": [{"username": "dimas", "name": "Mas Dimas"}]}
    cm, dc, _ = _patch_collections(contracts, users_by_team)
    with cm:
        await mig.main(apply=True)
    dc.update_one.assert_not_called()


@pytest.mark.asyncio
async def test_existing_stakeholder_with_different_role_does_not_block():
    """Dimas sudah stakeholder owner — tetap ditambah sebagai consumer (entry terpisah)."""
    contracts = [{
        "_id": "doc1",
        "contract_number": "CN-1",
        "metadata": {
            "consumer": [{"name": "penjualan"}],
            "stakeholders": [
                {"name": "Mas Dimas", "role": "owner", "username": "dimas"},
            ],
        },
    }]
    users_by_team = {"penjualan": [{"username": "dimas", "name": "Mas Dimas"}]}
    cm, dc, _ = _patch_collections(contracts, users_by_team)
    with cm:
        await mig.main(apply=True)
    new_stakeholders = dc.update_one.call_args.args[1]["$push"]["metadata.stakeholders"]["$each"]
    assert new_stakeholders == [
        {"name": "Mas Dimas", "role": "consumer", "username": "dimas"},
    ]


# ── Warnings ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_warning_when_no_user_matches_team(capsys):
    """consumer[].name yang tidak punya user matching → warning ke stdout, tidak fail."""
    contracts = [{
        "_id": "doc1",
        "contract_number": "CN-1",
        "metadata": {
            "consumer": [{"name": "tim-bubar"}],
            "stakeholders": [],
        },
    }]
    cm, dc, _ = _patch_collections(contracts, users_by_team={})
    with cm:
        rc = await mig.main(apply=True)
    assert rc == 0
    dc.update_one.assert_not_called()
    out = capsys.readouterr().out
    assert "tim-bubar" in out
    assert "Warning" in out
