from pydantic import BaseModel
from typing import List, Optional


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
    votes: List[Vote] = []
    status: str = "pending"   # "pending" | "approved" | "rejected"
    created_at: Optional[str] = None
    resolved_at: Optional[str] = None


class VoteRequest(BaseModel):
    vote: str                 # "approved" | "rejected"
    reason: Optional[str] = None
