from pydantic import BaseModel
from typing import Dict, List, Optional


class Vote(BaseModel):
    username: str
    vote: str           # "approved" | "rejected"
    reason: Optional[str] = None
    voted_at: Optional[str] = None


class ApprovalRecord(BaseModel):
    approval_id: str
    # Jenis pengajuan. Approval lama (sebelum issue #69) tidak punya field
    # ini → default "contract_change" untuk backward compat.
    type: str = "contract_change"     # contract_change | rule_catalog_create
    # ID generic — contract_number untuk perubahan kontrak,
    # rule code untuk pengajuan modul aturan baru.
    target_id: Optional[str] = None
    # Legacy field — masih ada untuk approval contract_change.
    # Optional di model supaya approval rule_catalog_create yang tidak punya
    # contract_number tetap lolos validasi.
    contract_number: Optional[str] = None
    requested_by: str
    proposed_changes: dict
    approvers: List[str]
    # ADR-0005 (supersedes ADR-0004): derivasi approver per peran. Untuk
    # contract: owner/producer/consumer. Untuk rule_catalog_create: steward
    # (admin/root). Approval lama tetap dihormati lewat logika fallback di
    # voting endpoint.
    approvers_by_role: Optional[Dict[str, List[str]]] = None
    fallback_roles: List[str] = []
    votes: List[Vote] = []
    status: str = "pending"   # "pending" | "approved" | "rejected"
    created_at: Optional[str] = None
    resolved_at: Optional[str] = None


class VoteRequest(BaseModel):
    vote: str                 # "approved" | "rejected"
    reason: Optional[str] = None
