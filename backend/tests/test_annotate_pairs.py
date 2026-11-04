"""
Tests for backend/scripts/annotate_pairs.py — the phonetics annotation pass.

Covers schema shape (matches sarvam_train.jsonl / MLOpsPipeline.export_anonymized_sft_dataset),
manifest parsing, corrective vs error modes, error-type coverage bias, dry-run vs
emit, unknown manifests skipped, empty-text skipped, and the summary diagnostics block.
The production phonetics_engine.analyze is a no-op stub in tests — tests verify the
script's routing and output shape, not engine accuracy.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

import pytest

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "annotate_pairs.py"
spec = importlib.util.spec_from_file_location("annotate_pairs", SCRIPT_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def write_manifest(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n",
        encoding="utf-8",
    )


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


# --- fixture isolation; engine is a no-op before emit (see import) ----------
@pytest.fixture(autouse=True)
def _noop_engine(monkeypatch):
    """Keep the real phonetics engine out of the test process."""
    from backend.app.services import phonetics_engine as pe
    from backend.app.services.phonetics_engine import PhoneticsDiagnosticEngine

    def stub_analyze(self, target, spoken, language=None, **kw):
        return {
            "target_phonemes": "target",
            "spoken_phonemes": "spoken",
            "accuracy_score": 0.0,
            "clinical_feedback": "clinical",
        }

    real_diag = getattr(PhoneticsDiagnosticEngine, "analyze", None)
    PhoneticsDiagnosticEngine.analyze = stub_analyze

    # annotate_pairs imports the module singleton via:
    #   from backend.app.services.phonetics_engine import phonetics_engine
    # That names the instance object. Patch that same imported object.
    if hasattr(pe, "analyze"):
        orig_pe_analyze = pe.analyze
        pe.analyze = stub_analyze
        yield
        pe.analyze = orig_pe_analyze
    else:
        yield

    if real_diag is not None:
        PhoneticsDiagnosticEngine.analyze = real_diag


# --- schema -------------------------------------------------------------------
def _fixture_args(tmp_path, manifest_name, text_lines, correct_frac=0.0, dry_run=False, out_name=None):
    manifest = tmp_path / manifest_name
    write_manifest(manifest, text_lines)
    if out_name is None:
        out = tmp_path / f"out_{manifest_name}_results"
    else:
        out = tmp_path / out_name
    args = argparse.Namespace(
        dry_run=dry_run,
        correct_frac=correct_frac,
        seed=1,
        limit_per_lang=0,
        dataset_dir=manifest.parent,
        manifests=[manifest],
        output_dir=out,
    )
    return manifest, out, args


def test_record_matches_sarvam_train_schema(tmp_path):
    manifest, out, args = _fixture_args(
        tmp_path, "manifest_en-In_train.jsonl",
        [{"audio_filepath": "a.wav", "text": "rabbit"}],
        correct_frac=0.0,
    )
    emitted = mod.annotate_file(manifest, out, args, Counter(), Counter())
    assert emitted == 1
    out_file = out / "phonetics_pairs_en-In_train.jsonl"
    assert out_file.exists()
    rec = read_jsonl(out_file)[0]
    assert set(rec) >= {"instruction", "input", "output"}
    assert rec["instruction"] == mod.INSTRUCTION
    assert rec["input"].startswith("Target Phrase: rabbit")
    assert "Spoken Phrase:" in rec["input"]
    assert "Target Phonemes:" in rec["input"]
    assert "Spoken Phonemes:" in rec["input"]
    assert rec["output"] == "clinical"
    meta = rec["meta"]
    assert meta["language"] == "en-In"
    assert meta["split"] == "train"
    assert meta["error_mode"] == "error"
    assert isinstance(meta["uid"], str) and len(meta["uid"].split("_", 1)[1]) == 12
    assert isinstance(meta["injected"], list)
    assert meta["accuracy_score"] == 0.0
    assert meta["source_audio"] == "a.wav"


def test_uid_is_deterministic(tmp_path):
    manifest, out, args = _fixture_args(
        tmp_path, "manifest_xx_train.jsonl",
        [{"audio_filepath": "a.wav", "text": "rabbit"}],
    )
    emitted = mod.annotate_file(manifest, out, args, Counter(), Counter())
    assert emitted == 1
    out_file = out / "phonetics_pairs_xx_train.jsonl"
    assert out_file.exists()
    rec = read_jsonl(out_file)[0]
    assert mod.uid_for({"audio_filepath": "a.wav", "text": "rabbit", "language": "xx"}) == rec["meta"]["uid"]


# --- manifest parsing / routing ----------------------------------------------
def test_unrecognized_manifest_skipped(tmp_path):
    manifest = tmp_path / "manifest_bad.name"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text("{}", encoding="utf-8")
    out = tmp_path / "out"
    args = argparse.Namespace(
        dry_run=False, correct_frac=0.3, seed=1, limit_per_lang=0,
        dataset_dir=manifest.parent, manifests=[manifest], output_dir=out,
    )
    emitted = mod.annotate_file(manifest, out, args, Counter(), Counter())
    assert emitted == 0
    stats = Counter()
    mod.annotate_file(manifest, out, args, stats, Counter())
    assert stats["skipped_unrecognized_manifest"] == 1


def test_empty_text_rows_skipped(tmp_path):
    manifest = tmp_path / "manifest_hi_train.jsonl"
    write_manifest(manifest, [
        {"audio_filepath": "a.wav", "text": "good row"},
        {"audio_filepath": "b.wav", "text": "   "},
        {"audio_filepath": "c.wav", "text": ""},
    ])
    out = tmp_path / "out"
    dummy = Counter()
    emitted = mod.annotate_file(manifest, out, argparse.Namespace(
        dry_run=True, correct_frac=1.0, seed=1, limit_per_lang=0,
        dataset_dir=manifest.parent, manifests=[manifest], output_dir=out,
    ), dummy, Counter())
    assert emitted == 1
    assert dummy["hi:skipped_empty_text"] == 2


def test_dry_run_prints_but_does_not_write(tmp_path, capsys):
    manifest = tmp_path / "manifest_vi_train.jsonl"
    write_manifest(manifest, [{"audio_filepath": "a.wav", "text": "xin chào"}])
    out = tmp_path / "out"
    args = argparse.Namespace(
        dry_run=True, correct_frac=0.0, seed=1, limit_per_lang=0,
        dataset_dir=manifest.parent, manifests=[manifest], output_dir=out,
    )
    mod.annotate_file(manifest, out, args, Counter(), Counter())
    captured = capsys.readouterr()
    assert "dry-run: would write 1 pairs" in captured.out
    assert not out.exists()


def test_correct_mode_keeps_target_in_spoken(tmp_path):
    manifest = tmp_path / "manifest_en-US_train.jsonl"
    write_manifest(manifest, [{"audio_filepath": "a.wav", "text": "sunshine"}])
    out = tmp_path / "out"
    args = argparse.Namespace(
        dry_run=False, correct_frac=1.0, seed=1, limit_per_lang=0,
        dataset_dir=manifest.parent, manifests=[manifest], output_dir=out,
    )
    mod.annotate_file(manifest, out, args, Counter(), Counter())
    rec = read_jsonl(out / "phonetics_pairs_en-US_train.jsonl")[0]
    assert rec["meta"]["error_mode"] == "correct"
    assert rec["meta"]["injected"] == []
    assert rec["input"].splitlines()[1] == "Spoken Phrase: sunshine"


def test_correct_frac_sent_rounding(tmp_path):
    # With correct_frac=1.0 every row is correct; with 0.0 every row is error.
    # Use Devanagari-script texts whose consonants match DEVANAGARI_PATTERNS, so the
    # error path always finds a pattern under correct_frac=0.0.
    manifest_path = tmp_path / "manifest_mr_train.jsonl"
    rows = [
        {"audio_filepath": "a.wav", "text": "\u0930\u093e\u092e"},  # r\u00e2m
        {"audio_filepath": "b.wav", "text": "\u0916\u093e\u0928"},  # kh\u00e2n
        {"audio_filepath": "c.wav", "text": "\u091f\u093e\u091f"},  # T\u00e2.T\u00e2
    ]
    write_manifest(manifest_path, rows)
    out = tmp_path / "out_err"
    manifest_path2 = tmp_path / "manifest_mr_train.jsonl"
    write_manifest(manifest_path2, rows)
    stats = Counter()
    mod.annotate_file(manifest_path, out, argparse.Namespace(
        dry_run=True, correct_frac=0.0, seed=1, limit_per_lang=0,
        dataset_dir=manifest_path.parent, manifests=[manifest_path], output_dir=out,
    ), stats, Counter())
    assert stats["mr:error_mode"] == 3
    assert stats["mr:correct_mode"] == 0

    out2 = tmp_path / "out_corr"
    stats2 = Counter()
    write_manifest(manifest_path2, rows)
    mod.annotate_file(manifest_path2, out2, argparse.Namespace(
        dry_run=True, correct_frac=1.0, seed=1, limit_per_lang=0,
        dataset_dir=manifest_path2.parent, manifests=[manifest_path2], output_dir=out2,
    ), stats2, Counter())
    assert stats2["mr:correct_mode"] == 3
    assert stats2["mr:error_mode"] == 0


# --- error-type coverage bias ------------------------------------------------
def test_pick_pattern_prefers_least_covered_script(tmp_path):
    lang = "en-In"
    texts = ["grass fox", "star sat", "breeze zone", "very fine", "kitten gut"]
    manifests = tmp_path / "per_lang"
    mpath = manifests / f"manifest_{lang}_train.jsonl"
    write_manifest(mpath, [{"audio_filepath": f"{i}.wav", "text": t} for i, t in enumerate(texts)])
    out = tmp_path / "out"
    # Force very-low coverage on a specific error type so pick_pattern homes in on it
    coverage = Counter()
    coverage["velar_fronting"] = 0
    coverage["frontal_lisp"] = 10
    coverage["stopping"] = 10
    rows = mpath.read_text(encoding="utf-8").splitlines()
    chosen = []
    for row in [json.loads(line) for line in rows if line.strip()]:
        p = mod.pick_pattern(row["text"], coverage, __import__("random").Random(7))
        if p:
            chosen.append(p[2])
            coverage[p[2]] += 1
        else:
            chosen.append(None)
    # First k/ fronting match should win (lowest coverage), once chosen coverage rises
    assert chosen
    assert "velar_fronting" in chosen
    idx = chosen.index("velar_fronting")
    assert chosen[idx] == "velar_fronting"


def test_pick_pattern_returns_none_when_no_pattern_matches(tmp_path):
    # Text with only digits/punctuation and no consonant match for latin/devanagari patterns
    mpath = tmp_path / "manifest_zz_train.jsonl"
    write_manifest(mpath, [{"audio_filepath": "a.wav", "text": "--- 123 !!!"}])
    coverage = Counter()
    p = mod.pick_pattern("--- 123 !!!", coverage, __import__("random").Random(1))
    assert p is None


def test_build_pair_uses_module_engine(tmp_path):
    row = {"audio_filepath": "a.wav", "text": "bass", "language": "en-IN"}
    coverage = Counter()
    rec = mod.build_pair(row, "en-IN", "train", "error",
                         mod.LATIN_PATTERNS[0], None, coverage)
    assert rec["meta"]["error_mode"] == "error"
    assert rec["meta"]["injected"] == [mod.LATIN_PATTERNS[0][2]]
    assert coverage[mod.LATIN_PATTERNS[0][2]] == 1


# --- limit_per_lang -----------------------------------------------------------
def test_limit_per_lang_caps_emission(tmp_path):
    mpath = tmp_path / "manifest_ja_train.jsonl"
    write_manifest(mpath, [
        {"audio_filepath": f"{i}.wav", "text": f"row{i}"}
        for i in range(20)
    ])
    out = tmp_path / "out"
    stats = Counter()
    emitted = mod.annotate_file(mpath, out, argparse.Namespace(
        dry_run=False, correct_frac=1.0, seed=1, limit_per_lang=5,
        dataset_dir=mpath.parent, manifests=[mpath], output_dir=out,
    ), stats, Counter())
    assert emitted == 5
    assert len(read_jsonl(out / "phonetics_pairs_ja_train.jsonl")) == 5


# --- main / summary -----------------------------------------------------------
def test_main_no_manifests_prints_and_exits_one(capsys):
    orig_argv = sys.argv
    try:
        sys.argv = ["annotate_pairs.py"]
        rc = mod.main()
        assert rc == 1
        captured = capsys.readouterr()
        assert "No manifests found" in captured.err, repr(captured.err)
    finally:
        sys.argv = orig_argv


def test_main_parse_args_rejects_bad_correct_frac():
    with pytest.raises(SystemExit):
        mod.argparse.ArgumentParser().parse_args(["--correct-frac", "1.5", "--dataset-dir", "/tmp"])


def test_summary_contains_diagnostics_keys(tmp_path, monkeypatch):
    manifest = tmp_path / "manifest_mr_train.jsonl"
    write_manifest(manifest, [{"audio_filepath": "a.wav", "text": "राम"}])
    out = tmp_path / "out"
    orig_argv = sys.argv
    try:
        monkeypatch.setattr(sys, "argv", [
            "annotate_pairs.py",
            "--dataset-dir", str(manifest.parent),
            "--output-dir", str(out),
            "--correct-frac", "0.0",
            "--seed", "1",
        ])
        rc = mod.main()
        assert rc == 0
        summary_path = out / "annotation_summary.json"
        assert summary_path.exists()
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        assert summary["dry_run"] is False
        assert summary["correct_frac"] == 0.0
        assert summary["seed"] == 1
        assert "mr:train_written" in summary["totals"]
        assert "mr:error_mode" in summary["modes"]
        assert summary["error_type_coverage"]
    finally:
        sys.argv = orig_argv


def test_error_type_coverage_counter_populated(tmp_path):
    manifest = tmp_path / "manifest_en-In_train.jsonl"
    write_manifest(manifest, [{"audio_filepath": "a.wav", "text": "rabbit"}])
    out = tmp_path / "out"
    coverage = Counter()
    args = argparse.Namespace(
        dry_run=False, correct_frac=0.0, seed=1, limit_per_lang=0,
        dataset_dir=manifest.parent, manifests=[manifest], output_dir=out,
    )
    emitted = mod.annotate_file(manifest, out, args, Counter(), coverage)
    assert emitted == 1
    assert any(k in coverage for k in {"gliding_r", "velar_fronting", "frontal_lisp", "stopping", "th_fronting"})


def test_devagaradi_pattern_list_has_retroflex_fronting():
    assert any(fam == "retroflex_fronting" for _, _, fam in mod.DEVANAGARI_PATTERNS)
    assert any(fam == "aspiration_loss" for _, _, fam in mod.DEVANAGARI_PATTERNS)


def test_latin_pattern_list_has_stopping():
    assert any(fam == "stopping" for _, _, fam in mod.LATIN_PATTERNS)


def test_apply_error_first_match_only():
    text = "thriller thrill"
    pat = (r"\bth", "t", "th_fronting")
    corrupted, hits = mod.apply_error(text, pat, __import__("random").Random(0))
    assert hits == 1
    assert corrupted == "triller thrill"


def test_uid_for_language_prefix(tmp_path):
    uid = mod.uid_for({"audio_filepath": "a.wav", "text": "hi", "language": "ta-IN"})
    assert uid.startswith("ta-IN_")
