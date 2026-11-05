import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from backend.app.db.base import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


def get_utc_now() -> datetime:
    return datetime.now(UTC)


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="patient")  # "therapist", "patient", "admin"
    preferred_locale = Column(String(20), default="en-IN")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)

    # Relationships
    sessions_as_therapist = relationship("TherapySession", foreign_keys="TherapySession.therapist_id", back_populates="therapist")
    sessions_as_patient = relationship("TherapySession", foreign_keys="TherapySession.patient_id", back_populates="patient")
    consent = relationship("ConsentRecord", back_populates="user", uselist=False)


class TherapySession(Base):
    __tablename__ = "therapy_sessions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    therapist_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    patient_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    target_language = Column(String(20), default="hi")  # hi, kn, ta, te, en
    status = Column(String(50), default="active")       # active, completed, paused
    clinical_notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)
    updated_at = Column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)

    # Relationships
    therapist = relationship("User", foreign_keys=[therapist_id], back_populates="sessions_as_therapist")
    patient = relationship("User", foreign_keys=[patient_id], back_populates="sessions_as_patient")
    attempts = relationship("ExerciseAttempt", back_populates="session", cascade="all, delete-orphan")


class ExerciseAttempt(Base):
    __tablename__ = "exercise_attempts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    session_id = Column(String(36), ForeignKey("therapy_sessions.id"), nullable=False, index=True)
    target_phrase = Column(String(500), nullable=False)
    spoken_phrase = Column(String(500), nullable=True)
    target_phonemes = Column(String(500), nullable=True)
    spoken_phonemes = Column(String(500), nullable=True)
    is_correct = Column(Boolean, default=False)
    target_achieved = Column(Boolean, default=False)
    accuracy_score = Column(Float, default=0.0)
    errors_json = Column(Text, nullable=True)  # JSON array of error objects
    audio_storage_key = Column(String(500), nullable=True)
    source_language = Column(String(20), default="hi")
    translated_text = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)

    # Relationship
    session = relationship("TherapySession", back_populates="attempts")


class ConsentRecord(Base):
    __tablename__ = "consent_records"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), unique=True, nullable=False)
    hipaa_acknowledged = Column(Boolean, default=False)
    audio_retention_agreed = Column(Boolean, default=False)
    research_sft_permitted = Column(Boolean, default=False)
    consented_at = Column(DateTime(timezone=True), default=get_utc_now)

    user = relationship("User", back_populates="consent")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), nullable=True, index=True)
    action = Column(String(100), nullable=False)  # e.g., "AUDIO_ACCESSED", "EXPORT_SFT"
    resource = Column(String(255), nullable=False)
    ip_address = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)
