"""
IndicAST Clinical Memory Service
=================================
Shared clinical memory layer that persists per-patient phoneme error patterns,
mastery vectors, and adaptive tutor context across all features.

Storage: Redis (primary) → in-memory dict (offline fallback)
Privacy: Redis keys use hashed patient_id — no raw PII in key-space.

Consumed by:
  - exercises.py (after each ExerciseAttempt)
  - main.py     (after process_session_audio on /ws/live-ast)
  - main.py     (/ws/live-tutor WebSocket — adaptive coaching loop)
  - memory API  (/api/v1/memory endpoints)
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

class PatientMemory(BaseModel):
    """Full clinical memory record for one patient + dialect combination."""
    patient_id: str                        # de-identified hash
    dialect: str                           # "hi" | "kn" | "ta" | "te" | "en-IN"
    phoneme_errors: dict[str, int]         # {"P": 7, "K_VELAR": 3, ...}
    mastery_scores: dict[str, float]       # {"P": 0.45, "K_VELAR": 0.80, ...}
    weak_phonemes_ranked: list[str]        # top-N phonemes ranked by error freq
    recent_utterances: list[dict[str, Any]]  # last 5 spoken/target pairs
    total_sessions: int
    total_attempts: int
    consecutive_correct: int               # for tutor escalation logic
    consecutive_incorrect: int             # for tutor de-escalation logic
    last_updated: str                      # ISO 8601

    @classmethod
    def empty(cls, patient_id: str, dialect: str) -> "PatientMemory":
        return cls(
            patient_id=patient_id,
            dialect=dialect,
            phoneme_errors={},
            mastery_scores={},
            weak_phonemes_ranked=[],
            recent_utterances=[],
            total_sessions=0,
            total_attempts=0,
            consecutive_correct=0,
            consecutive_incorrect=0,
            last_updated=datetime.now(timezone.utc).isoformat(),
        )


class TutorContext(BaseModel):
    """Lightweight context snapshot fed into the Live Tutor loop."""
    patient_id: str
    dialect: str
    weak_phonemes: list[str]
    recent_targets: list[str]
    consecutive_correct: int
    consecutive_incorrect: int
    mastery_scores: dict[str, float]


# ---------------------------------------------------------------------------
# Memory Service
# ---------------------------------------------------------------------------

class MemoryService:
    """
    Redis-backed clinical memory with in-memory fallback for offline/CI mode.

    Key schema: indicast:memory:{dialect}:{sha256(patient_id)[:16]}
    TTL: 30 days (rolling on every update)
    """

    REDIS_TTL_SECONDS = 30 * 24 * 3600  # 30 days

    def __init__(self) -> None:
        self._redis: Any = None          # redis.asyncio.Redis | None
        self._memory_cache: dict[str, PatientMemory] = {}  # offline fallback
        self._redis_available = False

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def connect(self) -> None:
        """Attempt to establish Redis connection; fall back to in-memory silently."""
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        try:
            import redis.asyncio as aioredis  # type: ignore[import-untyped]
            client = aioredis.from_url(redis_url, decode_responses=True, socket_connect_timeout=2)
            await client.ping()
            self._redis = client
            self._redis_available = True
            logger.info(f"[MemoryService] Redis connected at {redis_url}")
        except Exception as e:
            logger.warning(f"[MemoryService] Redis unavailable ({e}); using in-memory fallback")
            self._redis_available = False

    async def disconnect(self) -> None:
        if self._redis and self._redis_available:
            await self._redis.aclose()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _make_key(patient_id: str, dialect: str) -> str:
        """De-identified Redis key — patient UUID is hashed."""
        hashed = hashlib.sha256(patient_id.encode()).hexdigest()[:16]
        return f"indicast:memory:{dialect}:{hashed}"

    async def _load(self, patient_id: str, dialect: str) -> PatientMemory:
        key = self._make_key(patient_id, dialect)
        if self._redis_available:
            try:
                raw = await self._redis.get(key)
                if raw:
                    data = json.loads(raw)
                    # patient_id in payload is the hash — keep as-is
                    return PatientMemory(**data)
            except Exception as e:
                logger.warning(f"[MemoryService] Redis read failed: {e}")
        # Fallback
        return self._memory_cache.get(key, PatientMemory.empty(patient_id, dialect))

    async def _save(self, memory: PatientMemory, patient_id: str, dialect: str) -> None:
        key = self._make_key(patient_id, dialect)
        payload = memory.model_dump_json()
        if self._redis_available:
            try:
                await self._redis.set(key, payload, ex=self.REDIS_TTL_SECONDS)
                return
            except Exception as e:
                logger.warning(f"[MemoryService] Redis write failed: {e}")
        # Fallback
        self._memory_cache[key] = memory

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def get_memory(self, patient_id: str, dialect: str) -> PatientMemory:
        """Return full PatientMemory for a patient+dialect pair."""
        return await self._load(patient_id, dialect)

    async def get_weak_phonemes(
        self, patient_id: str, dialect: str, top_n: int = 3
    ) -> list[str]:
        """Return top-N phonemes with highest error counts."""
        mem = await self._load(patient_id, dialect)
        return mem.weak_phonemes_ranked[:top_n]

    async def get_tutor_context(self, patient_id: str, dialect: str) -> TutorContext:
        """Return a compact context snapshot for the Live Tutor loop."""
        mem = await self._load(patient_id, dialect)
        recent_targets = [u.get("target", "") for u in mem.recent_utterances[-5:]]
        return TutorContext(
            patient_id=patient_id,
            dialect=dialect,
            weak_phonemes=mem.weak_phonemes_ranked[:5],
            recent_targets=recent_targets,
            consecutive_correct=mem.consecutive_correct,
            consecutive_incorrect=mem.consecutive_incorrect,
            mastery_scores=mem.mastery_scores,
        )

    async def update_from_diagnostic(
        self,
        patient_id: str,
        dialect: str,
        diagnostic: dict[str, Any],
    ) -> PatientMemory:
        """
        Update memory from a live diagnostic result (from process_session_audio).

        Called after every ExerciseAttempt and after every /ws/live-ast "stop" event.
        """
        mem = await self._load(patient_id, dialect)

        target = diagnostic.get("target", "")
        spoken = diagnostic.get("spoken", "")
        is_correct = diagnostic.get("is_correct", False)
        errors = diagnostic.get("errors", [])

        # 1. Update phoneme error counts
        for error in errors:
            ph = error.get("target_slice", "").strip().upper()
            if ph:
                mem.phoneme_errors[ph] = mem.phoneme_errors.get(ph, 0) + 1

        # 2. Update mastery scores (exponential moving average α=0.3)
        alpha = 0.3
        target_phonemes = diagnostic.get("target_phonemes", "").split()
        for ph in target_phonemes:
            current = mem.mastery_scores.get(ph, 0.5)
            new_val = current * (1 - alpha) + (1.0 if is_correct else 0.0) * alpha
            mem.mastery_scores[ph] = round(new_val, 4)

        # 3. Recompute ranked weak phonemes
        mem.weak_phonemes_ranked = sorted(
            mem.phoneme_errors, key=mem.phoneme_errors.get, reverse=True  # type: ignore
        )

        # 4. Update recent utterances (rolling window of 10)
        mem.recent_utterances.append({
            "target": target,
            "spoken": spoken,
            "is_correct": is_correct,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        mem.recent_utterances = mem.recent_utterances[-10:]

        # 5. Update streak counters
        if is_correct:
            mem.consecutive_correct += 1
            mem.consecutive_incorrect = 0
        else:
            mem.consecutive_incorrect += 1
            mem.consecutive_correct = 0

        # 6. Update totals
        mem.total_attempts += 1
        mem.last_updated = datetime.now(timezone.utc).isoformat()

        await self._save(mem, patient_id, dialect)
        return mem

    async def increment_session_count(self, patient_id: str, dialect: str) -> None:
        """Increment total_sessions counter when a new therapy session starts."""
        mem = await self._load(patient_id, dialect)
        mem.total_sessions += 1
        mem.last_updated = datetime.now(timezone.utc).isoformat()
        await self._save(mem, patient_id, dialect)

    async def bulk_update_analytics(
        self,
        patient_id: str,
        dialect: str,
        phoneme_errors: dict[str, int],
        mastery_scores: dict[str, float],
    ) -> None:
        """
        Called by the Celery batch analytics task to overwrite aggregated stats.
        Preserves streak counters and recent utterances.
        """
        mem = await self._load(patient_id, dialect)
        mem.phoneme_errors = phoneme_errors
        mem.mastery_scores = mastery_scores
        mem.weak_phonemes_ranked = sorted(phoneme_errors, key=phoneme_errors.get, reverse=True)  # type: ignore
        mem.last_updated = datetime.now(timezone.utc).isoformat()
        await self._save(mem, patient_id, dialect)

    async def reset_memory(self, patient_id: str, dialect: str) -> PatientMemory:
        """Reset all memory for a patient+dialect (e.g., HIPAA deletion request)."""
        fresh = PatientMemory.empty(patient_id, dialect)
        await self._save(fresh, patient_id, dialect)
        logger.info(f"[MemoryService] Reset memory for patient_hash={patient_id[:8]}, dialect={dialect}")
        return fresh


# Singleton instance — imported throughout the app
memory_service = MemoryService()
