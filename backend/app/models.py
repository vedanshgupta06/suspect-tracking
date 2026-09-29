import datetime as dt

from sqlalchemy import (Boolean, Column, DateTime, Float, ForeignKey, Integer,
                         LargeBinary, String, Text)
from sqlalchemy.orm import relationship

from .database import Base

ROLES = ("admin", "police", "court", "custody")
LIFECYCLE_STATUSES = ("arrested", "remand", "chargesheet_filed", "trial",
                      "convicted", "acquitted", "custody", "released")


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(String, nullable=False)  # one of ROLES
    created_at = Column(DateTime, default=dt.datetime.utcnow)


class Token(Base):
    __tablename__ = "tokens"
    id = Column(Integer, primary_key=True)
    token = Column(String, unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    user = relationship("User")


class Suspect(Base):
    __tablename__ = "suspects"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    alias = Column(String, nullable=True)
    photo_path = Column(String, nullable=True)
    face_embedding = Column(LargeBinary, nullable=True)  # float32 bytes
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=dt.datetime.utcnow)

    lifecycle_events = relationship("LifecycleEvent", back_populates="suspect",
                                     order_by="LifecycleEvent.timestamp")
    cases = relationship("Case", back_populates="suspect")


class LifecycleEvent(Base):
    __tablename__ = "lifecycle_events"
    id = Column(Integer, primary_key=True)
    suspect_id = Column(Integer, ForeignKey("suspects.id"), nullable=False)
    status = Column(String, nullable=False)  # one of LIFECYCLE_STATUSES
    notes = Column(Text, nullable=True)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    timestamp = Column(DateTime, default=dt.datetime.utcnow)

    suspect = relationship("Suspect", back_populates="lifecycle_events")


class Case(Base):
    __tablename__ = "cases"
    id = Column(Integer, primary_key=True)
    fir_number = Column(String, unique=True, nullable=False, index=True)
    mo_text = Column(Text, nullable=False)
    location = Column(String, nullable=True)
    suspect_id = Column(Integer, ForeignKey("suspects.id"), nullable=True)
    status = Column(String, default="unsolved")  # unsolved | linked | closed
    fir_embedding = Column(LargeBinary, nullable=True)  # float32 bytes
    filed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    filed_at = Column(DateTime, default=dt.datetime.utcnow)

    suspect = relationship("Suspect", back_populates="cases")


class CaseLink(Base):
    """Stored suggestion from the FIR linker, kept for audit / demo purposes."""
    __tablename__ = "case_links"
    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    linked_case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    score = Column(Float, nullable=False)
    confirmed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=dt.datetime.utcnow)
