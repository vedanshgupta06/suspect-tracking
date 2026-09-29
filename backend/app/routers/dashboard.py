from collections import Counter

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import schemas
from ..database import get_db
from ..deps import get_current_user
from ..models import Case, CaseLink, LifecycleEvent, Suspect, User

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=schemas.DashboardSummary)
def summary(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    suspects = db.query(Suspect).all()
    status_counts = Counter()
    for s in suspects:
        last = (db.query(LifecycleEvent).filter(LifecycleEvent.suspect_id == s.id)
                .order_by(LifecycleEvent.timestamp.desc()).first())
        status_counts[last.status if last else "unknown"] += 1

    total_cases = db.query(Case).count()
    unsolved = db.query(Case).filter(Case.status == "unsolved").count()
    recent_links = db.query(CaseLink).count()

    return schemas.DashboardSummary(
        total_suspects=len(suspects), total_cases=total_cases,
        suspects_by_status=dict(status_counts), unsolved_cases=unsolved,
        recent_case_links=recent_links)
