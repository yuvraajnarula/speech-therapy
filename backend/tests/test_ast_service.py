import pytest
import numpy as np
from backend.app.services.live_ast_service import live_ast_service, VoiceActivityDetector


def test_vad_silence_detection():
    vad = VoiceActivityDetector(energy_threshold=300.0)
    silence = np.zeros(1600, dtype=np.int16).tobytes()
    assert vad.is_speech(silence) is False


def test_vad_speech_detection():
    vad = VoiceActivityDetector(energy_threshold=300.0)
    # Loud sine wave / audio energy
    t = np.linspace(0, 1, 1600)
    audio = (np.sin(2 * np.pi * 440 * t) * 10000).astype(np.int16).tobytes()
    assert vad.is_speech(audio) is True


def test_pcm_to_wav_header():
    dummy_pcm = np.zeros(1600, dtype=np.int16).tobytes()
    wav_io = live_ast_service.pcm_to_wav(dummy_pcm)
    data = wav_io.getvalue()
    # Check valid RIFF/WAVE header
    assert data[:4] == b"RIFF"
    assert data[8:12] == b"WAVE"


def test_indic_translation_lookup():
    translated = live_ast_service.translate_indic_speech(
        text="namaste",
        source_language="hi",
        target_language="en"
    )
    assert "Hello / Greetings" in translated


def test_process_session_audio_structure(monkeypatch):
    monkeypatch.setattr(live_ast_service, "transcribe", lambda pcm_bytes, language=None: "namaste")
    dummy_pcm = np.zeros(1600, dtype=np.int16).tobytes()
    res = live_ast_service.process_session_audio(
        pcm_bytes=dummy_pcm,
        target_text="namaste",
        source_language="hi",
        target_language="en"
    )
    assert "spoken" in res
    assert "target" in res
    assert "translated_text" in res
    assert "accuracy_score" in res
    assert "clinical_feedback" in res
