"""
Tests for backend/app/services/phonetics_engine.py — phonetic articulation diagnosis.

Covers: clean_phonemes (Indic dictionary, pronouncing library, fallback), analyze
(SequenceMatcher diff, accuracy score, target_achieved, clinical feedback), and
generate_clinical_feedback (substitution/omission/insertion bullets).
"""
import pytest

from backend.app.services.phonetics_engine import (
    PhoneticsDiagnosticEngine,
    phonetics_engine,
    INDIC_PHONETIC_MAP,
    PHONEME_ARTICULATION_GUIDE,
)


# ---------------------------------------------------------------------------
# clean_phonemes
# ---------------------------------------------------------------------------

def test_clean_phonemes_indic_dictionary_hit():
    engine = PhoneticsDiagnosticEngine()
    # namaste is in INDIC_PHONETIC_MAP
    result = engine.clean_phonemes("namaste", language="hi")
    assert result == "".join(INDIC_PHONETIC_MAP["namaste"])


def test_clean_phonemes_indic_dictionary_case_insensitive():
    engine = PhoneticsDiagnosticEngine()
    result = engine.clean_phonemes("Namaste", language="hi")
    assert result == "".join(INDIC_PHONETIC_MAP["namaste"])


def test_clean_phonemes_empty_string():
    engine = PhoneticsDiagnosticEngine()
    assert engine.clean_phonemes("", language="en") == ""
    assert engine.clean_phonemes("   ", language="en") == ""


def test_clean_phonemes_punctuation_stripped():
    engine = PhoneticsDiagnosticEngine()
    result = engine.clean_phonemes("Hello, world!", language="en")
    assert "," not in result
    assert "!" not in result


def test_clean_phonemes_fallback_approximation():
    engine = PhoneticsDiagnosticEngine()
    # "cat" is not in INDIC_PHONETIC_MAP; fallback maps c->C, a->AH, t->T
    result = engine.clean_phonemes("cat", language="en")
    assert result == "CAHT" or result == "CAT"


# ---------------------------------------------------------------------------
# analyze
# ---------------------------------------------------------------------------

def test_analyze_exact_match_is_correct():
    engine = PhoneticsDiagnosticEngine()
    result = engine.analyze("hello", "hello", language="en")
    assert result["is_correct"] is True
    assert result["target_achieved"] is True
    assert result["errors"] == []
    assert result["accuracy_score"] == 100.0


def test_analyze_substitution_error():
    engine = PhoneticsDiagnosticEngine()
    result = engine.analyze("rabbit", "wabbit", language="en")
    assert result["is_correct"] is False
    assert len(result["errors"]) > 0
    assert result["errors"][0]["type"] == "replace"
    assert result["accuracy_score"] < 100.0


def test_analyze_omission_error():
    engine = PhoneticsDiagnosticEngine()
    result = engine.analyze("stop", "top", language="en")
    assert result["is_correct"] is False
    delete_errors = [e for e in result["errors"] if e["type"] == "delete"]
    assert len(delete_errors) > 0


def test_analyze_insertion_error():
    engine = PhoneticsDiagnosticEngine()
    result = engine.analyze("cat", "cats", language="en")
    assert result["is_correct"] is False
    insert_errors = [e for e in result["errors"] if e["type"] == "insert"]
    assert len(insert_errors) > 0


def test_analyze_target_achieved_prefix_match():
    engine = PhoneticsDiagnosticEngine()
    result = engine.analyze("cat", "caterpillar", language="en")
    assert result["target_achieved"] is True


def test_analyze_return_schema():
    engine = PhoneticsDiagnosticEngine()
    result = engine.analyze("hello", "hallo", language="en")
    required_keys = {"target", "spoken", "language", "target_phonemes",
                     "spoken_phonemes", "is_correct", "target_achieved",
                     "accuracy_score", "errors", "clinical_feedback"}
    assert required_keys.issubset(result.keys())
    assert isinstance(result["errors"], list)
    assert isinstance(result["accuracy_score"], float)
    assert 0.0 <= result["accuracy_score"] <= 100.0


def test_analyze_accuracy_score_range():
    engine = PhoneticsDiagnosticEngine()
    for target, spoken in [("hello", "hello"), ("hello", "hallo"), ("hello", "xyzzy")]:
        result = engine.analyze(target, spoken, language="en")
        assert 0.0 <= result["accuracy_score"] <= 100.0


# ---------------------------------------------------------------------------
# generate_clinical_feedback
# ---------------------------------------------------------------------------

def test_generate_clinical_feedback_correct():
    engine = PhoneticsDiagnosticEngine()
    feedback = engine.generate_clinical_feedback(
        target_text="hello", spoken_text="hello",
        target_phonemes="HHAHLOW", spoken_phonemes="HHAHLOW",
        errors=[], target_achieved=True, is_correct=True,
    )
    assert "Accurate articulation" in feedback


def test_generate_clinical_feedback_substitution():
    engine = PhoneticsDiagnosticEngine()
    feedback = engine.generate_clinical_feedback(
        target_text="rabbit", spoken_text="wabbit",
        target_phonemes="R", spoken_phonemes="W",
        errors=[{"type": "replace", "target_slice": "R", "spoken_slice": "W"}],
        target_achieved=False, is_correct=False,
    )
    assert "Substitution" in feedback


def test_generate_clinical_feedback_omission():
    engine = PhoneticsDiagnosticEngine()
    feedback = engine.generate_clinical_feedback(
        target_text="stop", spoken_text="top",
        target_phonemes="ST", spoken_phonemes="T",
        errors=[{"type": "delete", "target_slice": "S", "spoken_slice": ""}],
        target_achieved=False, is_correct=False,
    )
    assert "Omission" in feedback


def test_generate_clinical_feedback_insertion():
    engine = PhoneticsDiagnosticEngine()
    feedback = engine.generate_clinical_feedback(
        target_text="cat", spoken_text="cats",
        target_phonemes="KT", spoken_phonemes="KTS",
        errors=[{"type": "insert", "target_slice": "", "spoken_slice": "S"}],
        target_achieved=False, is_correct=False,
    )
    assert "Insertion" in feedback


def test_generate_clinical_feedback_off_target():
    engine = PhoneticsDiagnosticEngine()
    # Spoken phonemes > 3x target length triggers off-target observation
    feedback = engine.generate_clinical_feedback(
        target_text="cat", spoken_text="elephant hippopotamus",
        target_phonemes="KT", spoken_phonemes="ELFNTXYZABC",
        errors=[], target_achieved=False, is_correct=False,
    )
    assert "Off-target" in feedback or "refocusing" in feedback


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

def test_phonetics_engine_singleton():
    assert isinstance(phonetics_engine, PhoneticsDiagnosticEngine)
