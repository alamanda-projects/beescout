"""
Tests untuk scripts/migrate_period_to_toplevel.py (#103).

Tidak butuh MongoDB — dccollection di-mock di level modul.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from scripts import migrate_period_to_toplevel as mig


def _cursor(docs):
    cur = MagicMock()
    cur.to_list = AsyncMock(return_value=list(docs))
    return cur


def _patch_dc(contracts: list):
    dc = AsyncMock()
    dc.find = MagicMock(return_value=_cursor(contracts))
    dc.update_one.return_value = None
    return patch.object(mig, "dccollection", dc), dc


# ── No-op ─────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_no_legacy_contracts(capsys):
    cm, dc = _patch_dc([])
    with cm:
        rc = await mig.main(apply=False)
    assert rc == 0
    dc.update_one.assert_not_called()
    assert "Tidak ada kontrak" in capsys.readouterr().out


# ── Dry-run ──────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_dry_run_prints_plan_no_writes(capsys):
    contracts = [{
        "_id": "doc1",
        "contract_number": "CN-1",
        "metadata": {"sla": {"effective_date": "2024-01-01", "end_of_contract": "2025-12-31"}},
    }]
    cm, dc = _patch_dc(contracts)
    with cm:
        rc = await mig.main(apply=False)
    assert rc == 0
    dc.update_one.assert_not_called()
    out = capsys.readouterr().out
    assert "DRY-RUN" in out
    assert "CN-1" in out


# ── Apply: promote + unset ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_apply_promotes_both_fields():
    contracts = [{
        "_id": "doc1",
        "contract_number": "CN-1",
        "metadata": {"sla": {"effective_date": "2024-01-01", "end_of_contract": "2025-12-31"}},
    }]
    cm, dc = _patch_dc(contracts)
    with cm:
        await mig.main(apply=True)
    dc.update_one.assert_called_once()
    _, update = dc.update_one.call_args.args
    assert update["$set"] == {
        "metadata.effective_date": "2024-01-01",
        "metadata.expiry_date": "2025-12-31",
    }
    assert update["$unset"] == {
        "metadata.sla.effective_date": "",
        "metadata.sla.end_of_contract": "",
    }


@pytest.mark.asyncio
async def test_apply_only_one_legacy_field():
    contracts = [{
        "_id": "doc1",
        "contract_number": "CN-1",
        "metadata": {"sla": {"end_of_contract": "2025-12-31"}},
    }]
    cm, dc = _patch_dc(contracts)
    with cm:
        await mig.main(apply=True)
    _, update = dc.update_one.call_args.args
    assert update["$set"] == {"metadata.expiry_date": "2025-12-31"}
    assert update["$unset"] == {"metadata.sla.end_of_contract": ""}


# ── Idempotency ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_idempoten_no_change_when_already_migrated():
    """Top-level sudah terisi & sla.* kosong → tidak query hit (find pakai
    $or sla.*), tapi kalau lewat (defensive) tetap tidak update."""
    contracts = [{
        "_id": "doc1",
        "contract_number": "CN-1",
        "metadata": {
            "effective_date": "2024-01-01",
            "expiry_date": "2025-12-31",
            "sla": {},
        },
    }]
    cm, dc = _patch_dc(contracts)
    with cm:
        await mig.main(apply=True)
    dc.update_one.assert_not_called()


@pytest.mark.asyncio
async def test_toplevel_wins_legacy_dropped_with_note(capsys):
    """Top-level sudah ada + legacy juga ada → top-level dipertahankan,
    legacy di-unset, ada catatan."""
    contracts = [{
        "_id": "doc1",
        "contract_number": "CN-1",
        "metadata": {
            "effective_date": "2024-06-15",
            "sla": {"effective_date": "2023-01-01"},
        },
    }]
    cm, dc = _patch_dc(contracts)
    with cm:
        await mig.main(apply=True)
    _, update = dc.update_one.call_args.args
    assert "metadata.effective_date" not in update.get("$set", {})
    assert update["$unset"] == {"metadata.sla.effective_date": ""}
    out = capsys.readouterr().out
    assert "top-level effective_date sudah ada" in out


# ── pending_changes also migrated ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_pending_changes_also_migrated():
    """Approval draft di pending_changes ikut tersinkron."""
    contracts = [{
        "_id": "doc1",
        "contract_number": "CN-1",
        "metadata": {"sla": {}},
        "pending_changes": {
            "metadata": {
                "sla": {"effective_date": "2026-01-01", "end_of_contract": "2027-12-31"},
            },
        },
    }]
    cm, dc = _patch_dc(contracts)
    with cm:
        await mig.main(apply=True)
    _, update = dc.update_one.call_args.args
    assert update["$set"] == {
        "pending_changes.metadata.effective_date": "2026-01-01",
        "pending_changes.metadata.expiry_date": "2027-12-31",
    }
    assert update["$unset"] == {
        "pending_changes.metadata.sla.effective_date": "",
        "pending_changes.metadata.sla.end_of_contract": "",
    }
