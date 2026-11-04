"""
Tests for the Live Tutor service (adaptive target selection, encouragement
builder, per-connection session state) and its integration with the shared
clinical memory layer.
"""
import pytest

from backend.app.services.live_tutor_service import (
    LiveTutorSession,
    TUTOR_WORD_BANK,
    build_encouragement,
    phoneme_focus_for,
    select_tutor_target,
)
from backend.app.services.memory_service import PatientMemory


def _memory_from_attempts(attempts: list[dict]) -> PatientMemory:
    """Build a PatientMemory by replaying attempts through update_from_diagnostic logic."""
    mem = PatientMemory.empty("test-patient", "hi")
    for attempt in attempts:
        mem.total_attempts += 1
        for error in attempt.get("errors", []):
            ph = error.get("target_slice", "").strip().upper()
            if ph:
                mem.phoneme_errors[ph] = mem.phoneme_errors.get(ph, 0) + 1
        if attempt["is_correct"]:
            mem.consecutive_correct += 1
            mem.consecutive_incorrect = 0
        else:
            mem.consecutive_incorrect += 1
            mem.consecutive_correct = 0
        mem.recent_utterances.append({
            "target": attempt.get("target", ""),
            "spoken": attempt.get("spoken", ""),
            "is_correct": attempt["is_correct"],
            "timestamp": "2026-01-01T00:00:00+00:00",
        })
        mem.recent_utterances = mem.recent_utterances[-10:]
    mem.weak_phonemes_ranked = sorted(
        mem.phoneme_errors, key=mem.phoneme_errors.get, reverse=True  # type: ignore
    )
    return mem


# ---------------------------------------------------------------------------
# Target selection
# ---------------------------------------------------------------------------

def test_word_bank_covers_all_dialects():
    languages = {w["language"] for w in TUTOR_WORD_BANK}
    assert {"hi", "kn", "ta", "te", "en-IN"} <= languages


def test_target_selection_prefers_weak_phonemes():
    # The selector draws randomly from the top-3 scored candidates, so sample
    # repeated draws: khana is the only Hindi word containing KH and must always
    # be in that top-3 (non-appearance over 30 draws has p ≈ (2/3)^30 ≈ 5e-6).
    draws = {
        select_tutor_target(dialect="hi", weak_phonemes=["KH"], recent_targets=[])["word"]
        for _ in range(30)
    }
    assert "khana" in draws
    assert "KH" in TUTOR_WORD_BANK[[w["word"] for w in TUTOR_WORD_BANK].index("khana")]["phonemes"]


def test_target_selection_avoids_recent_targets():
    recent = ["khana", "ghar", "sapna"]
    for _ in range(20):
        target = select_tutor_target(dialect="hi", weak_phonemes=["N"], recent_targets=recent)
        assert target["word"] not in recent


def test_target_selection_falls_back_to_dialect_words():
    target = select_tutor_target(dialect="hi", weak_phonemes=[], recent_targets=[])
    assert target["language"] == "hi"


# ---------------------------------------------------------------------------
# Encouragement builder — streak-aware adaptive messaging
# ---------------------------------------------------------------------------

def test_encouragement_escalates_on_correct_streak():
    assert build_encouragement(True, consecutive_correct=1, consecutive_incorrect=0) == "Well done! Try the next word."
    assert build_encouragement(True, consecutive_correct=2, consecutive_incorrect=0) == "Great job! Keep the streak going."
    assert "harder" in build_encouragement(True, consecutive_correct=3, consecutive_incorrect=0)


def test_encouragement_deescalates_on_incorrect_streak():
    assert build_encouragement(False, consecutive_correct=0, consecutive_incorrect=1) == "Good try! Listen carefully and try again."
    assert build_encouragement(False, consecutive_correct=0, consecutive_incorrect=2) == "Almost there! Focus on the highlighted sound."
    assert "easier" in build_encouragement(False, consecutive_correct=0, consecutive_incorrect=3)


# ---------------------------------------------------------------------------
# Phoneme focus
# ---------------------------------------------------------------------------

def test_phoneme_focus_prefers_weak_phoneme_present_in_target():
    target = {"word": "khana", "phonemes": "KH AH N AH"}
    assert phoneme_focus_for(target, weak_phonemes=["KH", "P"]) == "KH"
    assert phoneme_focus_for(target, weak_phonemes=[]) == "KH"


def test_phoneme_focus_ignores_weak_phoneme_absent_from_target():
    target = {"word": "ghar", "phonemes": "G AH R"}
    assert phoneme_focus_for(target, weak_phonemes=["P"]) == "G"


# ---------------------------------------------------------------------------
# Per-connection session state machine
# ---------------------------------------------------------------------------

def test_tutor_session_lifecycle():
    session = LiveTutorSession()
    assert not session.started

    session.start("patient_1", "hi")
    session.current_target = TUTOR_WORD_BANK[0]
    assert session.started

    session.append_audio(b"\x00\x01\x00\x01")
    pcm = session.drain_audio()
    assert pcm == b"\x00\x01\x00\x01"
    assert session.drain_audio() == b""  # drained

    session.track_result(is_correct=True)
    session.track_result(is_correct=False)
    assert session.score == {"correct": 1, "total": 2}

    session.current_target = TUTOR_WORD_BANK[0]
    cue = session.first_cue_payload(TUTOR_WORD_BANK[0], weak_phonemes=["P"])
    assert cue["type"] == "tutor_cue"
    assert cue["phoneme_target"] == "P"

    session.current_target = TUTOR_WORD_BANK[0]
    feedback = session.feedback_payload(
        diagnostic={"is_correct": True},
        memory_snapshot={"consecutive_correct": 3, "consecutive_incorrect": 0},
        next_target=TUTOR_WORD_BANK[3],
        weak_phonemes=["KH"],
    )
    assert feedback["type"] == "feedback"
    assert feedback["session_score"] == {"correct": 1, "total": 2}
    assert "harder" in feedback["encouragement"]
    assert feedback["next_cue"]["target_word"] == "khana"

    completion = session.completion_payload()
    assert completion["type"] == "session_complete"


# ---------------------------------------------------------------------------
# Memory layer drives adaptive selection "in advance"
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_tutor_context_reflects_memory_learning(monkeypatch):
    """Weak phonemes recorded in memory must surface in tutor context."""
    from backend.app.services import live_tutor_service

    # Simulate a patient who keeps mispronouncing the K-family phonemes
    attempts = [
        {"is_correct": False, "target": "khana", "spoken": "tana",
         "errors": [{"type": "substitution", "target_slice": "K", "spoken_slice": "T"}]},
        {"is_correct": False, "target": "khana", "spoken": "tana",
         "errors": [{"type": "substitution", "target_slice": "K", "spoken_slice": "T"}]},
        {"is_correct": False, "target": "ghar", "spoken": "tar",
         "errors": [{"type": "substitution", "target_slice": "K", "spoken_slice": "T"}]},
    ]
    mem = _memory_from_attempts(attempts)

    # Use the real memory_service models directly instead of mocking Redis
    from backend.app.services.memory_service import TutorContext

    async def fake_get_tutor_context(patient_id, dialect):
        return TutorContext(
            patient_id=patient_id,
            dialect=dialect,
            weak_phonemes=mem.weak_phonemes_ranked[:5],
            recent_targets=[u.get("target", "") for u in mem.recent_utterances[-5:]],
            consecutive_correct=mem.consecutive_correct,
            consecutive_incorrect=mem.consecutive_incorrect,
            mastery_scores=mem.mastery_scores,
        )

    monkeypatch.setattr(live_tutor_service.memory_service, "get_tutor_context", fake_get_tutor_context)

    target, ctx = await live_tutor_service.get_adaptive_target("test-patient", "hi")

    assert ctx.weak_phonemes == ["K"]
    assert ctx.recent_targets == ["khana", "khana", "ghar"]
    # Recent targets are excluded by design (no immediate repeats), but once
    # khaana is off the recent list the selector must rank it top because it
    # is the only Hindi word containing the patient's weak K-family phoneme.
    top3 = {select_tutor_target("hi", ctx.weak_phonemes, ["ghar"])["word"] for _ in range(20)}
    assert "khana" in top3
