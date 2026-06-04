"""
Tests untuk scripts/migrate_backfill_model_description.py (#102 PR-B slice 4).

Tidak butuh MongoDB — koleksi di-mock di level modul.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from scripts import migrate_backfill_model_description as mig


def _cursor(docs):
    cur = MagicMock()
    cur.to_list = AsyncMock(return_value=list(docs))
    return cur


def _patch_collection(contracts: list):
    dc = AsyncMock()
    dc.find = MagicMock(return_value=_cursor(contracts))
    dc.update_one.return_value = None
    return patch.object(mig, "dccollection", dc), dc


# ── No-op cases ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_no_contracts_returns_quietly(capsys):
    cm, dc = _patch_collection([])
    with cm:
        rc = await mig.main(apply=False)
    assert rc == 0
    dc.update_one.assert_not_called()
    assert "Tidak ada kontrak" in capsys.readouterr().out


@pytest.mark.asyncio
async def test_dry_run_makes_no_writes(capsys):
    contracts = [{"_id": "d1", "contract_number": "CN-1",
                  "model": [{"column": "id"}]}]
    cm, dc = _patch_collection(contracts)
    with cm:
        rc = await mig.main(apply=False)
    assert rc == 0
    dc.update_one.assert_not_called()
    assert "DRY-RUN" in capsys.readouterr().out


# ── Apply mode ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_apply_backfills_empty_description():
    contracts = [{"_id": "d1", "contract_number": "CN-1",
                  "model": [{"column": "id", "business_name": "Identitas"}]}]
    cm, dc = _patch_collection(contracts)
    with cm:
        await mig.main(apply=True)
    dc.update_one.assert_called_once()
    patched = dc.update_one.call_args.args[1]["$set"]["model"]
    assert patched[0]["description"] == "(Otomatis dari nama: Identitas) — mohon dilengkapi"


@pytest.mark.asyncio
async def test_apply_uses_column_when_no_business_name():
    contracts = [{"_id": "d1", "contract_number": "CN-1",
                  "model": [{"column": "cust_id"}]}]
    cm, dc = _patch_collection(contracts)
    with cm:
        await mig.main(apply=True)
    patched = dc.update_one.call_args.args[1]["$set"]["model"]
    assert "cust_id" in patched[0]["description"]
    assert "mohon dilengkapi" in patched[0]["description"]


# ── Idempotency & skip ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_skip_column_with_existing_description():
    contracts = [{"_id": "d1", "contract_number": "CN-1",
                  "model": [{"column": "id", "description": "sudah ada"}]}]
    cm, dc = _patch_collection(contracts)
    with cm:
        await mig.main(apply=True)
    dc.update_one.assert_not_called()


@pytest.mark.asyncio
async def test_skip_column_without_name():
    """Baris kolom kosong (tanpa column) → tidak di-backfill."""
    contracts = [{"_id": "d1", "contract_number": "CN-1",
                  "model": [{"column": "", "description": ""}]}]
    cm, dc = _patch_collection(contracts)
    with cm:
        await mig.main(apply=True)
    dc.update_one.assert_not_called()


@pytest.mark.asyncio
async def test_mixed_columns_only_empty_backfilled():
    contracts = [{"_id": "d1", "contract_number": "CN-1",
                  "model": [
                      {"column": "id", "description": "ada"},
                      {"column": "name"},  # kosong → backfill
                  ]}]
    cm, dc = _patch_collection(contracts)
    with cm:
        await mig.main(apply=True)
    patched = dc.update_one.call_args.args[1]["$set"]["model"]
    assert patched[0]["description"] == "ada"
    assert "mohon dilengkapi" in patched[1]["description"]
