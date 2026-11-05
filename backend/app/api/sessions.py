from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.logging import audit_logger
from backend.app.core.security import TokenPayload, get_current_user, require_roles
from backend.app.db.models import ExerciseAttempt, TherapySession, User
from backend.app.db.session import get_db

router = APIRouter(prefix="/sessions", tags=["Therapy Sessions"])


class CreateSessionSchema(BaseModel):
    patient_id: str
    target_language: str = "hi"
    clinical_notes: str | None = None


class SessionResponseSchema(BaseModel):
    id: str
    therapist_id: str
    patient_id: str
    target_language: str
    status: str
    clinical_notes: str | None = None
    created_at: str


@router.post("/", response_model=SessionResponseSchema)
async def create_session(
    session_in: CreateSessionSchema,
    current_user: TokenPayload = Depends(require_roles(["therapist", "admin"])),
    db: AsyncSession = Depends(get_db)
):
    # Verify patient exists and has role 'patient'
    p_stmt = select(User).where(User.id == session_in.patient_id)
    p_res = await db.execute(p_stmt)
    patient = p_res.scalars().first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )

    session = TherapySession(
        therapist_id=current_user.sub,
        patient_id=session_in.patient_id,
        target_language=session_in.target_language,
        status="active",
        clinical_notes=session_in.clinical_notes,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    audit_logger.info(
        f"Therapy session created: id={session.id} by therapist={current_user.sub} for patient={session_in.patient_id}"
    )
    return SessionResponseSchema(
        id=session.id,
        therapist_id=session.therapist_id,
        patient_id=session.patient_id,
        target_language=session.target_language,
        status=session.status,
        clinical_notes=session.clinical_notes,
        created_at=session.created_at.isoformat(),
    )


@router.get("/")
async def list_sessions(
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.role == "therapist":
        stmt = select(TherapySession).where(TherapySession.therapist_id == current_user.sub)
    elif current_user.role == "patient":
        stmt = select(TherapySession).where(TherapySession.patient_id == current_user.sub)
    else:  # admin
        stmt = select(TherapySession)

    res = await db.execute(stmt)
    sessions = res.scalars().all()

    return [
        {
            "id": s.id,
            "therapist_id": s.therapist_id,
            "patient_id": s.patient_id,
            "target_language": s.target_language,
            "status": s.status,
            "clinical_notes": s.clinical_notes,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }
        for s in sessions
    ]


@router.get("/{session_id}")
async def get_session(
    session_id: str,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(TherapySession).where(TherapySession.id == session_id)
    res = await db.execute(stmt)
    session = res.scalars().first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    # Authorization guard: user must be the therapist or the patient
    if current_user.role != "admin" and session.therapist_id != current_user.sub and session.patient_id != current_user.sub:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access to session denied")

    # Fetch attempts
    att_stmt = select(ExerciseAttempt).where(ExerciseAttempt.session_id == session_id)
    att_res = await db.execute(att_stmt)
    attempts = att_res.scalars().all()

    return {
        "id": session.id,
        "therapist_id": session.therapist_id,
        "patient_id": session.patient_id,
        "target_language": session.target_language,
        "status": session.status,
        "clinical_notes": session.clinical_notes,
        "created_at": session.created_at.isoformat() if session.created_at else None,
        "attempts": [
            {
                "id": a.id,
                "target_phrase": a.target_phrase,
                "spoken_phrase": a.spoken_phrase,
                "target_phonemes": a.target_phonemes,
                "spoken_phonemes": a.spoken_phonemes,
                "is_correct": a.is_correct,
                "accuracy_score": a.accuracy_score,
                "errors": a.errors_json,
                "translated_text": a.translated_text,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in attempts
        ]
    }
