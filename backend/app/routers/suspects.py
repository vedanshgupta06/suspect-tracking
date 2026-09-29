from typing import List

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from .. import ml_services, schemas
from ..config import UPLOAD_DIR
from ..database import get_db
from ..deps import get_current_user, require_role
from ..models import LifecycleEvent, Suspect, User

router = APIRouter(prefix="/suspects", tags=["suspects"])


def _current_status(suspect: Suspect):
    return suspect.lifecycle_events[-1].status if suspect.lifecycle_events else None


def _to_out(suspect: Suspect) -> schemas.SuspectOut:
    out = schemas.SuspectOut.model_validate(suspect)
    out.current_status = _current_status(suspect)
    return out


@router.post("", response_model=schemas.SuspectCreateResponse)
def create_suspect(name: str = Form(...), alias: str = Form(None),
                    photo: UploadFile = File(...), db: Session = Depends(get_db),
                    user: User = Depends(require_role("police"))):
    """Arrest entry: stores the suspect, embeds the photo, and returns ranked alias/
    repeat-offender candidates found BEFORE this suspect is added to the gallery."""
    import os
    photo_bytes = photo.file.read()
    embedding = ml_services.embed_face_image(photo_bytes)

    candidates_raw = ml_services.search_face(embedding, top_k=5)
    id_to_suspect = {s.id: s for s in db.query(Suspect)
                      .filter(Suspect.id.in_([c["suspect_id"] for c in candidates_raw])).all()}
    candidates = [schemas.FaceMatchCandidate(
        suspect_id=c["suspect_id"], name=id_to_suspect[c["suspect_id"]].name,
        alias=id_to_suspect[c["suspect_id"]].alias, score=c["score"], is_match=c["is_match"]
    ) for c in candidates_raw if c["suspect_id"] in id_to_suspect]

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    photo_path = os.path.join(UPLOAD_DIR, f"suspect_{name.replace(' ', '_')}_{photo.filename}")
    with open(photo_path, "wb") as f:
        f.write(photo_bytes)

    suspect = Suspect(name=name, alias=alias, photo_path=photo_path,
                       face_embedding=ml_services.to_bytes(embedding), created_by=user.id)
    db.add(suspect)
    db.commit()
    db.refresh(suspect)
    db.add(LifecycleEvent(suspect_id=suspect.id, status="arrested", updated_by=user.id))
    db.commit()
    db.refresh(suspect)

    ml_services.add_face_to_gallery(suspect.id, embedding)
    return schemas.SuspectCreateResponse(suspect=_to_out(suspect), alias_candidates=candidates)


@router.get("", response_model=List[schemas.SuspectOut])
def list_suspects(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    return [_to_out(s) for s in db.query(Suspect).order_by(Suspect.id.desc()).all()]


@router.get("/{suspect_id}", response_model=schemas.SuspectOut)
def get_suspect(suspect_id: int, db: Session = Depends(get_db),
                 _user: User = Depends(get_current_user)):
    suspect = db.get(Suspect, suspect_id)
    if not suspect:
        raise HTTPException(404, "suspect not found")
    return _to_out(suspect)


@router.patch("/{suspect_id}/status", response_model=schemas.SuspectOut)
def update_status(suspect_id: int, body: schemas.StatusUpdateRequest,
                   db: Session = Depends(get_db),
                   user: User = Depends(require_role("police", "court", "custody"))):
    from ..models import LIFECYCLE_STATUSES
    if body.status not in LIFECYCLE_STATUSES:
        raise HTTPException(400, f"status must be one of {LIFECYCLE_STATUSES}")
    suspect = db.get(Suspect, suspect_id)
    if not suspect:
        raise HTTPException(404, "suspect not found")
    db.add(LifecycleEvent(suspect_id=suspect_id, status=body.status, notes=body.notes,
                           updated_by=user.id))
    db.commit()
    db.refresh(suspect)
    return _to_out(suspect)
