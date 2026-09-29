from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import schemas, security
from ..database import get_db
from ..deps import require_role
from ..models import User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=schemas.LoginResponse)
def login(body: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == body.username).first()
    if not user or not security.verify_password(body.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid username or password")
    token = security.create_token(db, user)
    return schemas.LoginResponse(token=token, role=user.role, full_name=user.full_name)


@router.post("/users", response_model=schemas.LoginResponse)
def create_user(body: schemas.UserCreate, db: Session = Depends(get_db),
                 _admin: User = Depends(require_role("admin"))):
    """Admin-only: create a police / court / custody / admin account."""
    if body.role not in ("admin", "police", "court", "custody"):
        raise HTTPException(400, "invalid role")
    if db.query(User).filter(User.username == body.username).first():
        raise HTTPException(400, "username already taken")
    user = User(username=body.username, full_name=body.full_name, role=body.role,
                password_hash=security.hash_password(body.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    token = security.create_token(db, user)
    return schemas.LoginResponse(token=token, role=user.role, full_name=user.full_name)
