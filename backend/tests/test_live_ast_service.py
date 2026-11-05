"""
Tests for backend/app/services/live_ast_service.py — live AST pipeline.

Covers: VoiceActivityDetector (energy/RMS speech detection), pcm_to_wav WAV
header wrapping, translate_indic_speech (dictionary + fallback), and
process_session_audio end-to-end (with mocked STT model).
"""
import io
import math
import struct
import wave
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from backend.app.services.live_ast_service import (
    LiveASTService,
    VoiceActivityDetector,
    INDIC_TRANSLATIONS,
    live_ast_service,
)


# ---------------------------------------------------------------------------
# VoiceActivityDetector
# ---------------------------------------------------------------------------

def test_vad_silence_returns_false():
    vad = VoiceActivityDetector(energy_threshold=300.0)
    silence = b"\x00\x00" * 100  # 100 zero samples
    assert vad.is_speech(silence) is False


def test_vad_loud_audio_returns_true():
    vad = VoiceActivityDetector(energy_threshold=300.0)
    # Generate a loud sine wave that exceeds RMS threshold
    rate = 16000
    frames = int(rate * 0.1)
    samples = [int(20000 * math.sin(2 * math.pi * 440 * i / rate)) for i in range(frames)]
    pcm = b"".join(struct.pack("<h", s) for s in samples)
    assert vad.is_speech(pcm) is True


def test_vad_empty_bytes_returns_false():
    vad = VoiceActivityDetector()
    assert vad.is_speech(b"") is False


def test_vad_single_byte_returns_false():
    vad = VoiceActivityDetector()
    assert vad.is_speech(b"\x00") is False


def test_vad_threshold_boundary():
    # Audio exactly at threshold should not exceed it
    vad = VoiceActivityDetector(energy_threshold=300.0)
    rate = 16000
    frames = int(rate * 0.1)
    # RMS of ~300 -> amplitude ~300 for constant signal
    samples = [300] * frames
    pcm = b"".join(struct.pack("<h", s) for s in samples)
    # RMS = 300, threshold = 300, not strictly greater
    assert vad.is_speech(pcm) is False


# ---------------------------------------------------------------------------
# pcm_to_wav
# ---------------------------------------------------------------------------

def test_pcm_to_wav_produces_valid_wav_header():
    svc = LiveASTService()
    pcm = b"\x00\x01" * 100  # 200 bytes = 100 samples
    wav_buf = svc.pcm_to_wav(pcm)
    wav_buf.seek(0)
    header = wav_buf.read(12)
    assert header[:4] == b"RIFF"
    assert header[8:12] == b"WAVE"

    # Re-open with stdlib wave to verify full validity
    wav_buf.seek(0)
    with wave.open(wav_buf, "rb") as w:
        assert w.getnchannels() == 1
        assert w.getsampwidth() == 2
        assert w.getframerate() == 16000
        assert w.getnframes() == 100


# ---------------------------------------------------------------------------
# translate_indic_speech
# ---------------------------------------------------------------------------

def test_translate_indic_hi_to_en_dictionary_hit():
    svc = LiveASTService()
    result = svc.translate_indic_speech("namaste", source_language="hi", target_language="en")
    assert result == "Hello / Greetings"


def test_translate_indic_hi_to_en_case_insensitive():
    svc = LiveASTService()
    result = svc.translate_indic_speech("NAMASTE", source_language="hi", target_language="en")
    assert result == "Hello / Greetings"


def test_translate_indic_kn_to_en_dictionary_hit():
    svc = LiveASTService()
    result = svc.translate_indic_speech("ನಮಸ್ಕಾರ", source_language="kn", target_language="en")
    assert result == "Hello / Greetings"


def test_translate_indic_no_match_returns_placeholder():
    svc = LiveASTService()
    result = svc.translate_indic_speech("unknown phrase", source_language="hi", target_language="en")
    assert result == "[Translation to EN]: unknown phrase"


def test_translate_indic_same_language_returns_text():
    svc = LiveASTService()
    result = svc.translate_indic_speech("namaste", source_language="hi", target_language="hi")
    assert result == "namaste"


def test_translate_indic_empty_returns_empty():
    svc = LiveASTService()
    result = svc.translate_indic_speech("", source_language="hi", target_language="en")
    assert result == ""


# ---------------------------------------------------------------------------
# process_session_audio (with mocked STT + phonetics)
# ---------------------------------------------------------------------------

def test_process_session_audio_full_pipeline(monkeypatch):
    svc = LiveASTService()

    # Mock the STT model to avoid downloading Whisper
    mock_model = MagicMock()
    mock_segment = MagicMock()
    mock_segment.text = "namaste"
    mock_model.transcribe.return_value = ([mock_segment], None)
    svc.stt_model = mock_model
    svc._model_loaded = True

    result = svc.process_session_audio(
        pcm_bytes=b"\x00\x01" * 100,
        target_text="namaste",
        source_language="hi",
        target_language="en",
    )

    assert result["spoken"] == "namaste"
    assert result["target"] == "namaste"
    assert result["source_language"] == "hi"
    assert result["target_language"] == "en"
    assert result["translated_text"] == "Hello / Greetings"
    assert "target_phonemes" in result
    assert "spoken_phonemes" in result
    assert "is_correct" in result
    assert "accuracy_score" in result
    assert "errors" in result
    assert "clinical_feedback" in result
    assert isinstance(result["errors"], list)


def test_process_session_audio_empty_audio_falls_back_to_target(monkeypatch):
    svc = LiveASTService()
    svc._model_loaded = True
    svc.stt_model = None  # no model -> fallback path

    result = svc.process_session_audio(
        pcm_bytes=b"",
        target_text="namaste",
        source_language="hi",
        target_language="en",
    )

    assert result["spoken"] == "namaste"  # falls back to target when unvoiced
    assert result["is_correct"] is True  # target == spoken


def test_process_session_audio_translation_fallback(monkeypatch):
    svc = LiveASTService()
    mock_model = MagicMock()
    mock_segment = MagicMock()
    mock_segment.text = "unknown phrase"
    mock_model.transcribe.return_value = ([mock_segment], None)
    svc.stt_model = mock_model
    svc._model_loaded = True

    result = svc.process_session_audio(
        pcm_bytes=b"\x00\x01" * 100,
        target_text="namaste",
        source_language="hi",
        target_language="en",
    )

    assert result["spoken"] == "unknown phrase"
    assert result["translated_text"] == "[Translation to EN]: unknown phrase"


# ---------------------------------------------------------------------------
# load_model in TESTING mode
# ---------------------------------------------------------------------------

def test_load_model_testing_mode(monkeypatch):
    monkeypatch.setenv("TESTING", "true")
    svc = LiveASTService()
    svc.stt_model = None
    svc._model_loaded = False
    svc.load_model()
    assert svc._model_loaded is True
    assert svc.stt_model is None


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

def test_live_ast_service_singleton():
    assert isinstance(live_ast_service, LiveASTService)
