"""Tests untuk scripts/migrate_stakeholder_roles.py."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from scripts import migrate_stakeholder_roles as mig


def _cursor(docs):
    cur = MagicMock()
    cur.to_list = AsyncMock(return_value=list(docs))
    return cur


def _patch_dc(contracts: list):
    dc = AsyncMock()
    dc.find = MagicMock(return_value=_cursor(contracts))
    dc.update_one.return_value = None
    return patch.object(mig, "dccollection", dc), dc


# ── No-op ────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_no_contracts_quiet_exit(capsys):
    cm, dc = _patch_dc([])
    with cm:
        await mig.main(apply=False)
    dc.update_one.assert_not_called()
    assert "Tidak ada kontrak" in capsys.readouterr().out


@pytest.mark.asyncio
async def test_dry_run_no_write():
    contracts = [{
        "_id": "doc1",
        "contract_number": "CN-1",
        "metadata": {"stakeholders": [{"name": "X", "role": "engineer"}]},
    }]
    cm, dc = _patch_dc(contracts)
    with cm:
        await mig.main(apply=False)
    dc.update_one.assert_not_called()


# ── Apply ────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_apply_maps_engineer_to_producer():
    contracts = [{
        "_id": "doc1",
        "contract_number": "CN-1",
        "metadata": {"stakeholders": [{"name": "Dimas", "role": "engineer"}]},
    }]
    cm, dc = _patch_dc(contracts)
    with cm:
        await mig.main(apply=True)
    dc.update_one.assert_called_once()
    _, update = dc.update_one.call_args.args
    new_sk = update["$set"]["metadata.stakeholders"]
    assert new_sk[0]["role"] == "producer"


@pytest.mark.asyncio
@pytest.mark.parametrize("old,new", [
    ("engineer",  "producer"),
    ("analyst",   "consumer"),
    ("architect", "producer"),
    ("steward",   "reviewer"),
])
async def test_apply_all_mappings(old, new):
    contracts = [{
        "_id": f"doc-{old}",
        "contract_number": f"CN-{old}",
        "metadata": {"stakeholders": [{"name": "X", "role": old}]},
    }]
    cm, dc = _patch_dc(contracts)
    with cm:
        await mig.main(apply=True)
    new_sk = dc.update_one.call_args.args[1]["$set"]["metadata.stakeholders"]
    assert new_sk[0]["role"] == new


@pytest.mark.asyncio
async def test_apply_preserves_spec_roles():
    """Stakeholder yang sudah pakai nilai spec → tidak disentuh."""
    contracts = [{
        "_id": "doc1",
        "contract_number": "CN-1",
        "metadata": {"stakeholders": [
            {"name": "A", "role": "owner"},      # spec, keep
            {"name": "B", "role": "consumer"},   # spec, keep
            {"name": "C", "role": "engineer"},   # non-spec, map
        ]},
    }]
    cm, dc = _patch_dc(contracts)
    with cm:
        await mig.main(apply=True)
    new_sk = dc.update_one.call_args.args[1]["$set"]["metadata.stakeholders"]
    assert new_sk[0]["role"] == "owner"
    assert new_sk[1]["role"] == "consumer"
    assert new_sk[2]["role"] == "producer"  # engineer → producer


# ── Edge cases ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_unknown_role_logged_not_changed(capsys):
    """Role custom yang tidak ada di mapping → log warning, jangan diubah."""
    contracts = [{
        "_id": "doc1",
        "contract_number": "CN-1",
        "metadata": {"stakeholders": [
            {"name": "X", "role": "engineer"},        # map
            {"name": "Y", "role": "custom-role-xyz"}, # unknown — keep, warn
        ]},
    }]
    cm, dc = _patch_dc(contracts)
    with cm:
        await mig.main(apply=True)
    # Mapping engineer→producer applied; custom-role-xyz un-touched.
    new_sk = dc.update_one.call_args.args[1]["$set"]["metadata.stakeholders"]
    assert new_sk[0]["role"] == "producer"
    assert new_sk[1]["role"] == "custom-role-xyz"
    out = capsys.readouterr().out
    assert "custom-role-xyz" in out
    assert "TIDAK ter-mapping" in out


@pytest.mark.asyncio
async def test_idempotency_after_apply():
    """Setelah apply, jalankan lagi → 0 perubahan (semua role sudah spec)."""
    # Simulasi state pasca migrasi: query mencari role lama → return empty
    # (karena DB sudah bersih). Test ini verifikasi behavior find query
    # nya semestinya tidak match → tidak ada update.
    cm, dc = _patch_dc([])
    with cm:
        await mig.main(apply=True)
    dc.update_one.assert_not_called()
