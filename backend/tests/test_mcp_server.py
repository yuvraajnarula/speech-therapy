import json

from backend.services.mcp_server import analyze_indian_context, evaluate_english_phonetics


def test_analyze_indian_context_match():
    result = json.loads(analyze_indian_context("namaste", "namaste", "hi"))
    assert result["language"] == "hi"
    assert result["is_correct"] is True


def test_analyze_indian_context_mismatch():
    result = json.loads(analyze_indian_context("namaste", "namaskar", "hi"))
    assert result["language"] == "hi"
    assert result["is_correct"] is False


def test_evaluate_english_phonetics_correct():
    result = json.loads(evaluate_english_phonetics("cat", "cat"))
    assert result["language"] == "en"
    assert result["is_correct"] is True
    assert result["target_achieved"] is True
    assert result["errors"] == []


def test_evaluate_english_phonetics_substitution():
    result = json.loads(evaluate_english_phonetics("cat", "bat"))
    assert result["language"] == "en"
    assert result["is_correct"] is False
    assert len(result["errors"]) > 0
    assert result["errors"][0]["type"] == "replace"


def test_evaluate_english_phonetics_unknown_word():
    result = json.loads(evaluate_english_phonetics("xyzq", "xyzq"))
    assert result["language"] == "en"
    assert result["is_correct"] is True
