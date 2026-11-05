import base64
import json

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.logging import audit_logger
from backend.app.core.security import TokenPayload, get_current_user, require_roles
from backend.app.db.models import ConsentRecord, ExerciseAttempt, TherapySession
from backend.app.db.session import get_db
from backend.app.services.live_ast_service import live_ast_service
from backend.app.services.mlops_pipeline import mlops_pipeline
from backend.app.services.storage_service import storage_service

router = APIRouter(prefix="/exercises", tags=["Exercises & Analytics"])


class ExerciseEvaluateRequest(BaseModel):
    session_id: str
    target_phrase: str
    audio_base64: str | None = None
    source_language: str = "hi"
    target_language: str = "en"


@router.post("/evaluate")
async def evaluate_exercise(
    req: ExerciseEvaluateRequest,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Verify session access
    s_stmt = select(TherapySession).where(TherapySession.id == req.session_id)
    s_res = await db.execute(s_stmt)
    session = s_res.scalars().first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    # Decode audio if provided
    pcm_bytes = b""
    storage_key = None
    if req.audio_base64:
        try:
            pcm_bytes = base64.b64decode(req.audio_base64)
        except Exception:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid audio base64")

    # Run AST and phonetic analysis
    result = live_ast_service.process_session_audio(
        pcm_bytes=pcm_bytes,
        target_text=req.target_phrase,
        source_language=req.source_language,
        target_language=req.target_language
    )

    # Check HIPAA consent before persistent audio storage
    c_stmt = select(ConsentRecord).where(ConsentRecord.user_id == current_user.sub)
    c_res = await db.execute(c_stmt)
    consent = c_res.scalars().first()

    if consent and consent.audio_retention_agreed and pcm_bytes:
        wav_buffer = live_ast_service.pcm_to_wav(pcm_bytes)
        storage_key = storage_service.upload_audio_bytes(wav_buffer.getvalue(), filename_prefix="attempt")

    # Save to database
    attempt = ExerciseAttempt(
        session_id=session.id,
        target_phrase=req.target_phrase,
        spoken_phrase=result["spoken"],
        target_phonemes=result["target_phonemes"],
        spoken_phonemes=result["spoken_phonemes"],
        is_correct=result["is_correct"],
        target_achieved=result["target_achieved"],
        accuracy_score=result["accuracy_score"],
        errors_json=json.dumps(result["errors"]),
        audio_storage_key=storage_key,
        source_language=req.source_language,
        translated_text=result["translated_text"],
    )
    db.add(attempt)
    await db.commit()
    await db.refresh(attempt)

    audit_logger.info(f"Exercise attempt logged: id={attempt.id}, score={attempt.accuracy_score}")

    return {
        "attempt_id": attempt.id,
        **result
    }


@router.get("/analytics/{patient_id}")
async def get_patient_analytics(
    patient_id: str,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.role == "patient" and current_user.sub != patient_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    # Retrieve all attempts for patient
    stmt = (
        select(ExerciseAttempt)
        .join(TherapySession)
        .where(TherapySession.patient_id == patient_id)
        .order_by(ExerciseAttempt.created_at.desc())
    )
    res = await db.execute(stmt)
    attempts = res.scalars().all()

    total_attempts = len(attempts)
    correct_attempts = sum(1 for a in attempts if a.is_correct)
    avg_score = round(sum(a.accuracy_score for a in attempts) / max(total_attempts, 1), 1)

    # Phoneme error breakdown
    substitution_count = 0
    omission_count = 0
    insertion_count = 0

    for a in attempts:
        if a.errors_json:
            try:
                errs = json.loads(a.errors_json)
                for e in errs:
                    e_type = e.get("type")
                    if e_type == "replace":
                        substitution_count += 1
                    elif e_type == "delete":
                        omission_count += 1
                    elif e_type == "insert":
                        insertion_count += 1
            except Exception:
                pass

    return {
        "patient_id": patient_id,
        "total_attempts": total_attempts,
        "correct_attempts": correct_attempts,
        "success_rate_percent": round((correct_attempts / max(total_attempts, 1)) * 100, 1),
        "average_accuracy_score": avg_score,
        "error_distribution": {
            "substitutions": substitution_count,
            "omissions": omission_count,
            "insertions": insertion_count,
        }
    }


@router.post("/export-sft")
async def export_sft_dataset(
    current_user: TokenPayload = Depends(require_roles(["therapist", "admin"])),
    db: AsyncSession = Depends(get_db)
):
    # Only export data for users who consented to research SFT
    stmt = (
        select(ExerciseAttempt)
        .join(TherapySession)
        .join(ConsentRecord, ConsentRecord.user_id == TherapySession.patient_id)
        .where(ConsentRecord.research_sft_permitted.is_(True))
    )
    res = await db.execute(stmt)
    attempts = res.scalars().all()

    export_data = [
        {
            "target_phrase": a.target_phrase,
            "spoken_phrase": a.spoken_phrase,
            "target_phonemes": a.target_phonemes,
            "spoken_phonemes": a.spoken_phonemes,
            "clinical_feedback": f"Phonetic accuracy: {a.accuracy_score}%.",
        }
        for a in attempts
    ]

    export_path = mlops_pipeline.export_anonymized_sft_dataset(export_data)
    audit_logger.info(f"Admin/Therapist {current_user.sub} exported SFT dataset to {export_path}")

    return {
        "status": "success",
        "exported_records": len(export_data),
        "file_path": str(export_path),
    }
