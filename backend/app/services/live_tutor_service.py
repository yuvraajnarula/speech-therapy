"""
Live Tutor Service — IndicAST Clinical Speech Therapy Platform
==============================================================
Adaptive real-time tutoring engine for the /ws/live-tutor WebSocket.

The tutor "learns as we go": every spoken attempt is pushed through the shared
clinical memory layer (memory_service), and the next drill target is selected
from the patient's rank-ordered weak phonemes. Because the memory layer is
shared with all other features (Live AST trials, exercise attempts, batch
analytics), the tutor warms up *in advance* of the next session — a patient
who struggled with /K/ in yesterday's trial gets K-heavy targets today,
before the therapist ever opens the tutor tab.

Adaptive difficulty rules:
  - Streak of correct answers  → escalate (prefer harder targets)
  - Streak of incorrect answers → de-escalate (prefer easier targets)

Consumed by:
  - main.py (/ws/live-tutor WebSocket loop)
  - backend/tests/test_live_tutor.py
"""
from __future__ import annotations

import random
from typing import Any, Optional

from backend.app.core.logging import app_logger
from backend.app.services.memory_service import memory_service, TutorContext

# ---------------------------------------------------------------------------
# Indic word bank for Live Tutor target selection (backend mirror of frontend)
# ---------------------------------------------------------------------------

TUTOR_WORD_BANK: list[dict] = [
    # Hindi
    {"word": "pani", "language": "hi", "phonemes": "P AE N IY", "native_script": "पानी", "ipa": "/paːniː/", "category": "daily"},
    {"word": "mama", "language": "hi", "phonemes": "M AH M AH", "native_script": "माँ", "ipa": "/maː/", "category": "family"},
    {"word": "baba", "language": "hi", "phonemes": "B AH B AH", "native_script": "बाबा", "ipa": "/baːbaː/", "category": "family"},
    {"word": "khana", "language": "hi", "phonemes": "KH AH N AH", "native_script": "खाना", "ipa": "/kʰaːnaː/", "category": "daily"},
    {"word": "ghar", "language": "hi", "phonemes": "G AH R", "native_script": "घर", "ipa": "/ɡʱər/", "category": "environment"},
    {"word": "sapna", "language": "hi", "phonemes": "S AH P N AH", "native_script": "सपना", "ipa": "/səpnaː/", "category": "abstract"},
    # Kannada
    {"word": "niru", "language": "kn", "phonemes": "N IH R UH", "native_script": "ನೀರು", "ipa": "/niːru/", "category": "daily"},
    {"word": "mane", "language": "kn", "phonemes": "M AH N EH", "native_script": "ಮನೆ", "ipa": "/mane/", "category": "environment"},
    # Tamil
    {"word": "thaai", "language": "ta", "phonemes": "T AH AY", "native_script": "தாய்", "ipa": "/t̪aːj/", "category": "family"},
    {"word": "thanneer", "language": "ta", "phonemes": "T AH N IH R", "native_script": "தண்ணீர்", "ipa": "/t̪əɳɳiːr/", "category": "daily"},
    # Telugu
    {"word": "neellu", "language": "te", "phonemes": "N IY L UH", "native_script": "నీళ్ళు", "ipa": "/niːɭɭu/", "category": "daily"},
    {"word": "intlu", "language": "te", "phonemes": "IH N T L UH", "native_script": "ఇంటిలు", "ipa": "/intlu/", "category": "environment"},
    # English (India)
    {"word": "milk", "language": "en-IN", "phonemes": "M IH L K", "native_script": "Milk", "ipa": "/mɪlk/", "category": "daily"},
    {"word": "three", "language": "en-IN", "phonemes": "TH R IY", "native_script": "Three", "ipa": "/θriː/", "category": "numbers"},
    {"word": "sing", "language": "en-IN", "phonemes": "S IH NG", "native_script": "Sing", "ipa": "/sɪŋ/", "category": "daily"},
    {"word": "thank you", "language": "en-IN", "phonemes": "TH AE NG K Y UW", "native_script": "Thank You", "ipa": "/θæŋk juː/", "category": "social"},
]


# ---------------------------------------------------------------------------
# Adaptive target selection
# ---------------------------------------------------------------------------

def select_tutor_target(
    dialect: str,
    weak_phonemes: list[str],
    recent_targets: list[str],
) -> dict:
    """
    Adaptive target selection:
    1. Prefer words containing the patient's weak phonemes
    2. Avoid recently used targets
    3. Fall back to any word in dialect (Hindi as cross-dialect fallback)
    """
    dialect_words = [w for w in TUTOR_WORD_BANK if w["language"] == dialect]
    if not dialect_words:
        dialect_words = [w for w in TUTOR_WORD_BANK if w["language"] == "hi"]

    # Avoid recently used
    fresh = [w for w in dialect_words if w["word"] not in recent_targets] or dialect_words

    # Score by overlap with weak phonemes
    if weak_phonemes:
        def score(word: dict) -> int:
            phoneme_str = word.get("phonemes", "")
            return sum(1 for ph in weak_phonemes if ph in phoneme_str)

        fresh_sorted = sorted(fresh, key=score, reverse=True)
        # Pick from top-3 candidates with some randomness to avoid monotony
        candidates = fresh_sorted[:3]
        return random.choice(candidates)

    return random.choice(fresh)


def build_encouragement(is_correct: bool, consecutive_correct: int, consecutive_incorrect: int) -> str:
    """Streak-aware coaching message shown after every attempt."""
    if is_correct:
        if consecutive_correct >= 3:
            return "Excellent! You're on a roll — moving to a harder target."
        elif consecutive_correct == 2:
            return "Great job! Keep the streak going."
        return "Well done! Try the next word."
    else:
        if consecutive_incorrect >= 3:
            return "Let's try something easier. You're doing great — keep practicing."
        elif consecutive_incorrect == 2:
            return "Almost there! Focus on the highlighted sound."
        return "Good try! Listen carefully and try again."


async def get_adaptive_target(
    patient_id: str,
    dialect: str,
) -> tuple[dict, TutorContext]:
    """
    Pull the patient's tutor context from the clinical memory layer and
    select the next adaptive drill target. Single source of truth for the
    /ws/live-tutor start and feedback loops.
    """
    ctx = await memory_service.get_tutor_context(patient_id, dialect)
    target = select_tutor_target(
        dialect=dialect,
        weak_phonemes=ctx.weak_phonemes,
        recent_targets=ctx.recent_targets,
    )
    return target, ctx


def phoneme_focus_for(target: dict, weak_phonemes: list[str]) -> str:
    """Phoneme the tutor highlights on the cue: weakest patient phoneme present in the target, else first target phoneme."""
    target_phonemes = target.get("phonemes", "").split()
    for ph in weak_phonemes:
        if ph in target.get("phonemes", ""):
            return ph
    return target_phonemes[0] if target_phonemes else ""


# ---------------------------------------------------------------------------
# Per-connection tutor session state
# ---------------------------------------------------------------------------

class LiveTutorSession:
    """
    Encapsulates the per-WebSocket-connection tutor state machine.
    The FastAPI websocket handler drives I/O; this class owns the logic.
    """

    def __init__(self) -> None:
        self.patient_id: Optional[str] = None
        self.dialect: str = "hi"
        self.audio_buffer = bytearray()
        self.current_target: Optional[dict] = None
        self.score = {"correct": 0, "total": 0}

    @property
    def started(self) -> bool:
        return self.current_target is not None and self.patient_id is not None

    def start(self, patient_id: str, dialect: str) -> None:
        self.patient_id = patient_id
        self.dialect = dialect
        self.audio_buffer = bytearray()
        self.score = {"correct": 0, "total": 0}

    def append_audio(self, chunk: bytes) -> None:
        self.audio_buffer.extend(chunk)

    def drain_audio(self) -> bytes:
        pcm = bytes(self.audio_buffer)
        self.audio_buffer = bytearray()
        return pcm

    def first_cue_payload(self, target: dict, weak_phonemes: list[str]) -> dict[str, Any]:
        return {
            "type": "tutor_cue",
            "target_word": target["word"],
            "phoneme_target": phoneme_focus_for(target, weak_phonemes),
            "cue_text": f"Say: {target['word']}",
            "native_script": target.get("native_script", ""),
            "ipa": target.get("ipa", ""),
            "category": target.get("category", ""),
            "session_score": self.score,
        }

    def track_result(self, is_correct: bool) -> None:
        self.score["total"] += 1
        if is_correct:
            self.score["correct"] += 1

    def feedback_payload(
        self,
        diagnostic: dict[str, Any],
        memory_snapshot: dict[str, Any],
        next_target: dict,
        weak_phonemes: list[str],
    ) -> dict[str, Any]:
        mem = memory_snapshot
        return {
            "type": "feedback",
            "diagnostic": diagnostic,
            "encouragement": build_encouragement(
                is_correct=diagnostic.get("is_correct", False),
                consecutive_correct=mem.get("consecutive_correct", 0),
                consecutive_incorrect=mem.get("consecutive_incorrect", 0),
            ),
            "session_score": self.score,
            "memory_snapshot": memory_snapshot,
            "next_cue": {
                "target_word": next_target["word"],
                "phoneme_target": phoneme_focus_for(next_target, weak_phonemes),
                "cue_text": f"Now try: {next_target['word']}",
                "native_script": next_target.get("native_script", ""),
                "ipa": next_target.get("ipa", ""),
            },
        }

    def completion_payload(self) -> dict[str, Any]:
        app_logger.info(
            f"Live Tutor session completed: patient_hash={str(self.patient_id)[:8]}..., "
            f"dialect={self.dialect}, score={self.score['correct']}/{self.score['total']}"
        )
        return {
            "type": "session_complete",
            "session_score": self.score,
            "message": "Great work! Session complete.",
        }
