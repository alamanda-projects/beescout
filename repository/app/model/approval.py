from pydantic import BaseModel
from typing import Dict, List, Optional


class Vote(BaseModel):
    username: str
    vote: str           # "approved" | "rejected"
    reason: Optional[str] = None
    voted_at: Optional[str] = None


class ApprovalRecord(BaseModel):
    approval_id: str
    contract_number: str
    requested_by: str
    proposed_changes: dict
    approvers: List[str]
    # ADR-0004: derivasi approver per peran. Kunci yang dipakai:
    # "steward" | "producer" | "consumer". Approval baru selalu mengisi field
    # ini. Approval lama (tanpa field) tetap dihormati lewat logika fallback
    # di voting endpoint.
    approvers_by_role: Optional[Dict[str, List[str]]] = None
    # Daftar peran yang dianggap auto-pass karena tidak punya approver
    # (mis. kontrak tanpa stakeholder consumer ber-username). Dipakai untuk
    # audit trail — bukan untuk logika voting tambahan.
    fallback_roles: List[str] = []
    votes: List[Vote] = []
    status: str = "pending"   # "pending" | "approved" | "rejected"
    created_at: Optional[str] = None
    resolved_at: Optional[str] = None


class VoteRequest(BaseModel):
    vote: str                 # "approved" | "rejected"
    reason: Optional[str] = None
