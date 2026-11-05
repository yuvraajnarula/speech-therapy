"""
Tests for backend/app/services/memory_service.py — clinical memory layer.

Covers: PatientMemory/TutorContext models, Redis+fallback storage,
update_from_diagnostic (EMA mastery, streak counters, weak phoneme ranking),
get_tutor_context, reset_memory (HIPAA deletion), increment_session_count,
bulk_update_analytics, and de-identified key hashing.
"""
import asyncio
import hashlib
from collections import Counter
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from backend.app.services.memory_service import (
    MemoryService,
    PatientMemory,
    TutorContext,
    memory_service,
)


# ---------------------------------------------------------------------------
# PatientMemory model
# ---------------------------------------------------------------------------

def test_patient_memory_empty_factory():
    mem = PatientMemory.empty("patient-123", "hi")
    assert mem.patient_id == "patient-123"
    assert mem.dialect == "hi"
    assert mem.phoneme_errors == {}
    assert mem.mastery_scores == {}
    assert mem.weak_phonemes_ranked == []
    assert mem.recent_utterances == []
    assert mem.total_sessions == 0
    assert mem.total_attempts == 0
    assert mem.consecutive_correct == 0
    assert mem.consecutive_incorrect == 0


def test_patient_memory_model_dump_and_load():
    mem = PatientMemory.empty("p1", "kn")
    mem.total_attempts = 5
    mem.consecutive_correct = 3
    mem.phoneme_errors = {"K": 2, "P": 1}
    mem.mastery_scores = {"K": 0.4}
    mem.weak_phonemes_ranked = ["K", "P"]

    data = mem.model_dump()
    restored = PatientMemory(**data)
    assert restored.patient_id == "p1"
    assert restored.total_attempts == 5
    assert restored.phoneme_errors == {"K": 2, "P": 1}


# ---------------------------------------------------------------------------
# MemoryService helpers
# ---------------------------------------------------------------------------

def test_make_key_is_deidentified():
    key = MemoryService._make_key("patient-abc-123", "hi")
    expected_hash = hashlib.sha256(b"patient-abc-123").hexdigest()[:16]
    assert key == f"indicast:memory:hi:{expected_hash}"
    assert "patient-abc-123" not in key  # raw PII not in key


@pytest.mark.asyncio
async def test_connect_uses_in_memory_fallback_when_redis_unavailable():
    svc = MemoryService()
    await svc.connect()
    assert svc._redis_available is False
    assert svc._redis is None
    await svc.disconnect()


@pytest.mark.asyncio
async def test_save_and_load_roundtrip_in_memory():
    svc = MemoryService()
    await svc.connect()
    assert svc._redis_available is False

    mem = await svc.get_memory("patient-1", "en-IN")
    assert isinstance(mem, PatientMemory)
    assert mem.patient_id == "patient-1"
    assert mem.dialect == "en-IN"

    await svc.disconnect()


# ---------------------------------------------------------------------------
# update_from_diagnostic
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_update_from_diagnostic_counts_phoneme_errors():
    svc = MemoryService()
    await svc.connect()

    diagnostic = {
        "target": "khana",
        "spoken": "tana",
        "is_correct": False,
        "errors": [
            {"type": "replace", "target_slice": "K", "spoken_slice": "T"},
        ],
        "target_phonemes": "K AH N AH",
    }
    mem = await svc.update_from_diagnostic("patient-1", "hi", diagnostic)

    assert mem.phoneme_errors.get("K") == 1
    assert mem.total_attempts == 1
    assert mem.consecutive_incorrect == 1
    assert mem.consecutive_correct == 0
    assert len(mem.recent_utterances) == 1
    assert mem.recent_utterances[0]["target"] == "khana"
    assert mem.recent_utterances[0]["is_correct"] is False

    await svc.disconnect()


@pytest.mark.asyncio
async def test_update_from_diagnostic_ema_mastery_scores():
    svc = MemoryService()
    await svc.connect()

    # First attempt: correct
    d1 = {"target": "khana", "spoken": "khana", "is_correct": True,
          "errors": [], "target_phonemes": "K AH N AH"}
    mem = await svc.update_from_diagnostic("patient-1", "hi", d1)
    assert mem.mastery_scores["K"] == 0.65  # 0.5*0.7 + 1.0*0.3

    # Second attempt: incorrect
    d2 = {"target": "khana", "spoken": "tana", "is_correct": False,
          "errors": [], "target_phonemes": "K AH N AH"}
    mem = await svc.update_from_diagnostic("patient-1", "hi", d2)
    assert mem.mastery_scores["K"] == round(0.65 * 0.7 + 0.0 * 0.3, 4)  # 0.455

    await svc.disconnect()


@pytest.mark.asyncio
async def test_update_from_diagnostic_weak_phonemes_ranked():
    svc = MemoryService()
    await svc.connect()

    diagnostics = [
        {"target": "khana", "spoken": "tana", "is_correct": False,
         "errors": [{"type": "replace", "target_slice": "K", "spoken_slice": "T"}],
         "target_phonemes": "K AH N AH"},
        {"target": "ghar", "spoken": "dar", "is_correct": False,
         "errors": [{"type": "replace", "target_slice": "G", "spoken_slice": "D"}],
         "target_phonemes": "G AH R"},
        {"target": "khana", "spoken": "tana", "is_correct": False,
         "errors": [{"type": "replace", "target_slice": "K", "spoken_slice": "T"}],
         "target_phonemes": "K AH N AH"},
    ]
    for d in diagnostics:
        await svc.update_from_diagnostic("patient-1", "hi", d)

    mem = await svc.get_memory("patient-1", "hi")
    assert mem.weak_phonemes_ranked == ["K", "G"]  # K has 2 errors, G has 1

    await svc.disconnect()


@pytest.mark.asyncio
async def test_update_from_diagnostic_streak_counters():
    svc = MemoryService()
    await svc.connect()

    await svc.update_from_diagnostic("patient-1", "hi", {
        "target": "a", "spoken": "a", "is_correct": True, "errors": [], "target_phonemes": "AH"})
    mem = await svc.get_memory("patient-1", "hi")
    assert mem.consecutive_correct == 1
    assert mem.consecutive_incorrect == 0

    await svc.update_from_diagnostic("patient-1", "hi", {
        "target": "a", "spoken": "b", "is_correct": False, "errors": [], "target_phonemes": "AH"})
    mem = await svc.get_memory("patient-1", "hi")
    assert mem.consecutive_correct == 0
    assert mem.consecutive_incorrect == 1

    await svc.disconnect()


@pytest.mark.asyncio
async def test_update_from_diagnostic_recent_utterances_window():
    svc = MemoryService()
    await svc.connect()

    for i in range(12):
        await svc.update_from_diagnostic("patient-1", "hi", {
            "target": f"word{i}", "spoken": f"word{i}", "is_correct": True,
            "errors": [], "target_phonemes": "AH"})

    mem = await svc.get_memory("patient-1", "hi")
    assert len(mem.recent_utterances) == 10  # rolling window of 10
    assert mem.recent_utterances[0]["target"] == "word2"
    assert mem.recent_utterances[-1]["target"] == "word11"

    await svc.disconnect()


# ---------------------------------------------------------------------------
# get_tutor_context
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_tutor_context_snapshot():
    svc = MemoryService()
    await svc.connect()

    await svc.update_from_diagnostic("patient-1", "hi", {
        "target": "khana", "spoken": "tana", "is_correct": False,
        "errors": [{"type": "replace", "target_slice": "K", "spoken_slice": "T"}],
        "target_phonemes": "K AH N AH"})

    ctx = await svc.get_tutor_context("patient-1", "hi")
    assert isinstance(ctx, TutorContext)
    assert ctx.patient_id == "patient-1"
    assert ctx.dialect == "hi"
    assert "K" in ctx.weak_phonemes
    assert ctx.consecutive_incorrect == 1

    await svc.disconnect()


# ---------------------------------------------------------------------------
# reset_memory (HIPAA deletion)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_reset_memory_clears_all_state():
    svc = MemoryService()
    await svc.connect()

    await svc.update_from_diagnostic("patient-1", "hi", {
        "target": "khana", "spoken": "tana", "is_correct": False,
        "errors": [{"type": "replace", "target_slice": "K", "spoken_slice": "T"}],
        "target_phonemes": "K AH N AH"})
    mem_before = await svc.get_memory("patient-1", "hi")
    assert mem_before.total_attempts == 1

    fresh = await svc.reset_memory("patient-1", "hi")
    assert fresh.total_attempts == 0
    assert fresh.phoneme_errors == {}
    assert fresh.consecutive_correct == 0
    assert fresh.consecutive_incorrect == 0

    mem_after = await svc.get_memory("patient-1", "hi")
    assert mem_after.total_attempts == 0

    await svc.disconnect()


# ---------------------------------------------------------------------------
# increment_session_count
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_increment_session_count():
    svc = MemoryService()
    await svc.connect()

    await svc.increment_session_count("patient-1", "hi")
    await svc.increment_session_count("patient-1", "hi")
    mem = await svc.get_memory("patient-1", "hi")
    assert mem.total_sessions == 2

    await svc.disconnect()


# ---------------------------------------------------------------------------
# bulk_update_analytics
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_bulk_update_analytics_overwrites_aggregates():
    svc = MemoryService()
    await svc.connect()

    await svc.update_from_diagnostic("patient-1", "hi", {
        "target": "khana", "spoken": "tana", "is_correct": False,
        "errors": [{"type": "replace", "target_slice": "K", "spoken_slice": "T"}],
        "target_phonemes": "K AH N AH"})

    await svc.bulk_update_analytics(
        "patient-1", "hi",
        phoneme_errors={"P": 5, "T": 3},
        mastery_scores={"P": 0.9, "T": 0.7},
    )
    mem = await svc.get_memory("patient-1", "hi")
    assert mem.phoneme_errors == {"P": 5, "T": 3}
    assert mem.mastery_scores == {"P": 0.9, "T": 0.7}
    assert mem.weak_phonemes_ranked == ["P", "T"]

    await svc.disconnect()


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

def test_memory_service_singleton():
    assert isinstance(memory_service, MemoryService)
