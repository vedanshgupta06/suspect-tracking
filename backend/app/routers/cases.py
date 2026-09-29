from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import ml_services, schemas
from ..database import get_db
from ..deps import get_current_user, require_role
from ..models import Case, CaseLink, User

router = APIRouter(prefix="/cases", tags=["cases"])


from pydantic import BaseModel
from typing import Optional


class CaseCreate(BaseModel):
    fir_number: str
    mo_text: str
    location: Optional[str] = None
    suspect_id: Optional[int] = None


@router.post("", response_model=schemas.CaseCreateResponse)
def create_case(body: CaseCreate, db: Session = Depends(get_db),
                 user: User = Depends(require_role("police"))):
    """Files a new FIR, embeds the narrative, and returns ranked unsolved-case suggestions
    found BEFORE this FIR is added to the linker's index."""
    if db.query(Case).filter(Case.fir_number == body.fir_number).first():
        raise HTTPException(400, "a case with this FIR number already exists")

    embedding = ml_services.embed_fir_text(body.mo_text)
    links_raw = ml_services.link_fir(embedding, top_k=5)
    id_to_case = {c.id: c for c in db.query(Case)
                  .filter(Case.id.in_([l["case_id"] for l in links_raw])).all()}
    links = [schemas.CaseLinkCandidate(
        case_id=l["case_id"], fir_number=id_to_case[l["case_id"]].fir_number,
        score=l["score"], is_link=l["is_link"]
    ) for l in links_raw if l["case_id"] in id_to_case]

    case = Case(fir_number=body.fir_number, mo_text=body.mo_text, location=body.location,
                suspect_id=body.suspect_id, status="unsolved",
                fir_embedding=ml_services.to_bytes(embedding), filed_by=user.id)
    db.add(case)
    db.commit()
    db.refresh(case)

    for l in links:
        if l.is_link:
            db.add(CaseLink(case_id=case.id, linked_case_id=l.case_id, score=l.score))
    if links:
        case.status = "linked" if any(l.is_link for l in links) else "unsolved"
        db.commit()
        db.refresh(case)

    ml_services.add_fir_to_linker(case.id, embedding)
    return schemas.CaseCreateResponse(case=schemas.CaseOut.model_validate(case), linked_cases=links)


@router.get("", response_model=List[schemas.CaseOut])
def list_cases(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    return db.query(Case).order_by(Case.id.desc()).all()


@router.get("/{case_id}", response_model=schemas.CaseOut)
def get_case(case_id: int, db: Session = Depends(get_db),
             _user: User = Depends(get_current_user)):
    case = db.get(Case, case_id)
    if not case:
        raise HTTPException(404, "case not found")
    return case


@router.get("/{case_id}/links", response_model=List[schemas.CaseLinkCandidate])
def get_case_links(case_id: int, db: Session = Depends(get_db),
                    _user: User = Depends(get_current_user)):
    rows = db.query(CaseLink).filter(CaseLink.case_id == case_id).all()
    out = []
    for r in rows:
        linked = db.get(Case, r.linked_case_id)
        if linked:
            out.append(schemas.CaseLinkCandidate(case_id=linked.id, fir_number=linked.fir_number,
                                                  score=r.score, is_link=True))
    return out
