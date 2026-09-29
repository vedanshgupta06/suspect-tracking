"""Minimal auth: PBKDF2 password hashing (stdlib only) + random bearer tokens stored in DB.
Good enough for a college prototype; swap for a real auth provider before any real deployment."""
import datetime as dt
import hashlib
import hmac
import os
import secrets

from sqlalchemy.orm import Session

from . import config
from .models import Token, User

ITERATIONS = 200_000


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), ITERATIONS)
    return f"{salt}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt, hexhash = stored.split("$")
    except ValueError:
        return False
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), ITERATIONS)
    return hmac.compare_digest(dk.hex(), hexhash)


def create_token(db: Session, user: User) -> str:
    tok = secrets.token_urlsafe(32)
    db.add(Token(token=tok, user_id=user.id,
                 expires_at=dt.datetime.utcnow() + dt.timedelta(hours=config.TOKEN_TTL_HOURS)))
    db.commit()
    return tok


def get_user_for_token(db: Session, token: str):
    row = db.query(Token).filter(Token.token == token).first()
    if not row or row.expires_at < dt.datetime.utcnow():
        return None
    return row.user
