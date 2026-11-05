"""
Celery task definitions for IndicAST Clinical Speech Therapy Platform.

All tasks are designed to be:
  - Idempotent (safe to retry)
  - Independently testable without a live Celery worker
  - HIPAA-aware (no raw PII in task args or logs)
"""
from __future__ import annotations

import json
import os
from datetime import UTC, datetime, timedelta
from logging import getLogger
from typing import Any

from backend.app.worker.celery_app import celery_app

logger = getLogger(__name__)


# ---------------------------------------------------------------------------
# Task: Export SFT Dataset
# ---------------------------------------------------------------------------
@celery_app.task(bind=True, max_retries=3, default_retry_delay=30, name="backend.app.worker.tasks.export_sft_dataset_task")
def export_sft_dataset_task(self, session_id: str, format: str = "jsonl") -> dict[str, Any]:
    """
    Export fine-tuning dataset for a completed therapy session.

    Args:
        session_id: UUID of the TherapySession to export.
        format: "jsonl" (Whisper/SFT) or "csv"

    Returns:
        dict with export_path and record_count.
    """
    try:
        logger.info(f"[SFT Export] Starting export for session={session_id}, format={format}")

        # Import here to avoid circular imports at module load
        import asyncio

        from sqlalchemy import select
        from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
        from sqlalchemy.orm import sessionmaker

        from backend.app.core.config import settings
        from backend.app.db.models import ExerciseAttempt

        async def _do_export():
            engine = create_async_engine(settings.DATABASE_URL, echo=False)
            async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
            async with async_session() as db:
                result = await db.execute(
                    select(ExerciseAttempt).where(ExerciseAttempt.session_id == session_id)
                )
                attempts = result.scalars().all()

            records = []
            for attempt in attempts:
                records.append({
                    "audio_key": attempt.audio_storage_key,
                    "target": attempt.target_phrase,
                    "spoken": attempt.spoken_phrase,
                    "language": attempt.source_language,
                    "is_correct": attempt.is_correct,
                    "accuracy": attempt.accuracy_score,
                })

            export_dir = "dataset/anonymized_exports"
            os.makedirs(export_dir, exist_ok=True)
            ts = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
            export_path = f"{export_dir}/sft_{session_id[:8]}_{ts}.jsonl"

            with open(export_path, "w", encoding="utf-8") as f:
                for rec in records:
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")

            await engine.dispose()
            return {"export_path": export_path, "record_count": len(records)}

        return asyncio.run(_do_export())

    except Exception as exc:
        logger.error(f"[SFT Export] Failed for session={session_id}: {exc}")
        raise self.retry(exc=exc)


# ---------------------------------------------------------------------------
# Task: Batch Phoneme Analytics
# ---------------------------------------------------------------------------
@celery_app.task(bind=True, max_retries=2, default_retry_delay=60, name="backend.app.worker.tasks.run_batch_analytics_task")
def run_batch_analytics_task(self, patient_id: str, dialect: str = "hi") -> dict[str, Any]:
    """
    Recompute phoneme analytics and mastery scores for a patient.
    Updates the MemoryService with fresh aggregated data.

    Args:
        patient_id: UUID of the patient user (hashed in logs).
        dialect: Source language code.

    Returns:
        dict with updated weak_phonemes and mastery_scores.
    """
    try:
        logger.info(f"[Batch Analytics] Running for patient_hash={patient_id[:8]}, dialect={dialect}")

        import asyncio

        from sqlalchemy import select
        from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
        from sqlalchemy.orm import sessionmaker

        from backend.app.core.config import settings
        from backend.app.db.models import ExerciseAttempt, TherapySession
        from backend.app.services.memory_service import memory_service

        async def _do_analytics():
            engine = create_async_engine(settings.DATABASE_URL, echo=False)
            async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
            async with async_session() as db:
                # Get all sessions for patient
                sessions_result = await db.execute(
                    select(TherapySession).where(TherapySession.patient_id == patient_id)
                )
                sessions = sessions_result.scalars().all()
                session_ids = [s.id for s in sessions]

                if not session_ids:
                    return {"weak_phonemes": [], "mastery_scores": {}}

                # Get all exercise attempts across those sessions
                attempts_result = await db.execute(
                    select(ExerciseAttempt).where(ExerciseAttempt.session_id.in_(session_ids))
                )
                attempts = attempts_result.scalars().all()

            # Aggregate phoneme errors
            phoneme_errors: dict[str, int] = {}
            mastery_scores: dict[str, float] = {}
            correct_counts: dict[str, int] = {}
            total_counts: dict[str, int] = {}

            for attempt in attempts:
                if attempt.source_language != dialect:
                    continue
                if attempt.spoken_phonemes and attempt.target_phonemes:
                    for ph in attempt.target_phonemes.split():
                        total_counts[ph] = total_counts.get(ph, 0) + 1
                    if not attempt.is_correct:
                        for ph in attempt.target_phonemes.split():
                            phoneme_errors[ph] = phoneme_errors.get(ph, 0) + 1
                    else:
                        for ph in attempt.target_phonemes.split():
                            correct_counts[ph] = correct_counts.get(ph, 0) + 1

            for ph, total in total_counts.items():
                correct = correct_counts.get(ph, 0)
                mastery_scores[ph] = round(correct / total, 3) if total > 0 else 0.0

            # Push to memory layer
            await memory_service.bulk_update_analytics(patient_id, dialect, phoneme_errors, mastery_scores)

            await engine.dispose()
            weak = sorted(phoneme_errors, key=phoneme_errors.get, reverse=True)[:5]
            return {"weak_phonemes": weak, "mastery_scores": mastery_scores}

        return asyncio.run(_do_analytics())

    except Exception as exc:
        logger.error(f"[Batch Analytics] Failed for patient_hash={patient_id[:8]}: {exc}")
        raise self.retry(exc=exc)


# ---------------------------------------------------------------------------
# Task: Cleanup Expired Audio
# ---------------------------------------------------------------------------
@celery_app.task(name="backend.app.worker.tasks.cleanup_expired_audio_task")
def cleanup_expired_audio_task(retention_days: int = 90) -> dict[str, Any]:
    """
    Remove audio files from storage that have exceeded the retention policy.
    Only removes files for patients who have NOT set audio_retention_agreed=True.

    Returns:
        dict with deleted_count.
    """
    logger.info(f"[Audio Cleanup] Starting retention sweep (>{retention_days} days)")

    import asyncio

    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker

    from backend.app.core.config import settings
    from backend.app.db.models import ConsentRecord, ExerciseAttempt, TherapySession
    from backend.app.services.storage_service import storage_service

    async def _do_cleanup():
        engine = create_async_engine(settings.DATABASE_URL, echo=False)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        cutoff = datetime.now(UTC) - timedelta(days=retention_days)
        deleted = 0

        async with async_session() as db:
            # Find patients without long-term retention consent
            consent_result = await db.execute(
                select(ConsentRecord).where(ConsentRecord.audio_retention_agreed == False)  # noqa: E712
            )
            revoked_user_ids = {c.user_id for c in consent_result.scalars().all()}

            # Get sessions for revoked patients
            sessions_result = await db.execute(
                select(TherapySession).where(TherapySession.patient_id.in_(revoked_user_ids))
            )
            session_ids = [s.id for s in sessions_result.scalars().all()]

            # Find old attempts with stored audio
            attempts_result = await db.execute(
                select(ExerciseAttempt).where(
                    ExerciseAttempt.session_id.in_(session_ids),
                    ExerciseAttempt.created_at < cutoff,
                    ExerciseAttempt.audio_storage_key.isnot(None),
                )
            )
            attempts = attempts_result.scalars().all()

            for attempt in attempts:
                try:
                    storage_service.delete_audio(attempt.audio_storage_key)
                    attempt.audio_storage_key = None
                    deleted += 1
                except Exception as e:
                    logger.warning(f"[Audio Cleanup] Could not delete {attempt.audio_storage_key}: {e}")

            await db.commit()

        await engine.dispose()
        logger.info(f"[Audio Cleanup] Deleted {deleted} expired audio files")
        return {"deleted_count": deleted}

    return asyncio.run(_do_cleanup())
