import datetime as dt
from typing import List, Optional

from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    token: str
    role: str
    full_name: str


class UserCreate(BaseModel):
    username: str
    password: str
    full_name: str
    role: str


class FaceMatchCandidate(BaseModel):
    suspect_id: int
    name: str
    alias: Optional[str] = None
    score: float
    is_match: bool


class LifecycleEventOut(BaseModel):
    status: str
    notes: Optional[str] = None
    timestamp: dt.datetime

    class Config:
        from_attributes = True


class SuspectOut(BaseModel):
    id: int
    name: str
    alias: Optional[str] = None
    photo_path: Optional[str] = None
    current_status: Optional[str] = None
    created_at: dt.datetime
    lifecycle_events: List[LifecycleEventOut] = []

    class Config:
        from_attributes = True


class SuspectCreateResponse(BaseModel):
    suspect: SuspectOut
    alias_candidates: List[FaceMatchCandidate]


class StatusUpdateRequest(BaseModel):
    status: str
    notes: Optional[str] = None


class CaseLinkCandidate(BaseModel):
    case_id: int
    fir_number: str
    score: float
    is_link: bool


class CaseOut(BaseModel):
    id: int
    fir_number: str
    mo_text: str
    location: Optional[str] = None
    suspect_id: Optional[int] = None
    status: str
    filed_at: dt.datetime

    class Config:
        from_attributes = True


class CaseCreateResponse(BaseModel):
    case: CaseOut
    linked_cases: List[CaseLinkCandidate]


class DashboardSummary(BaseModel):
    total_suspects: int
    total_cases: int
    suspects_by_status: dict
    unsolved_cases: int
    recent_case_links: int
