import pytest
from backend.app.services.phonetics_engine import phonetics_engine


def test_clean_phonemes_basic():
    phonemes = phonetics_engine.clean_phonemes("cat")
    assert isinstance(phonemes, str)
    assert len(phonemes) > 0


def test_clean_phonemes_indic():
    phonemes = phonetics_engine.clean_phonemes("namaste", language="hi")
    assert phonemes == "NAHMAHSTEY"


def test_exact_match_articulation():
    res = phonetics_engine.analyze(target_text="hello", spoken_text="hello")
    assert res["is_correct"] is True
    assert res["target_achieved"] is True
    assert len(res["errors"]) == 0
    assert res["accuracy_score"] == 100.0


def test_phoneme_substitution_error():
    # "bat" vs "cat" has a substitution error for B vs K
    res = phonetics_engine.analyze(target_text="bat", spoken_text="cat")
    assert res["is_correct"] is False
    assert any(e["type"] == "replace" for e in res["errors"])
    assert "Clinical Observation" in res["clinical_feedback"]


def test_phoneme_omission_error():
    # If target has more phonemes than spoken
    res = phonetics_engine.analyze(target_text="stop", spoken_text="top")
    assert res["is_correct"] is False
    assert any(e["type"] == "delete" for e in res["errors"])
