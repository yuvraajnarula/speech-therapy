"""
Tests for backend/scripts/ingest_indicvoices.py — the IndicVoices manifest
ingester. Covers column auto-detection, audio resolution (id stem scan and
explicit path column), drop diagnostics, relative-path manifests, the
deterministic train/val split, and corrupt-WAV handling.
"""
import argparse
import importlib.util
import json
import math
import struct
import wave
from pathlib import Path

import pytest

_SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "ingest_indicvoices.py"
_spec = importlib.util.spec_from_file_location("ingest_indicvoices", _SCRIPT_PATH)
ingest = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ingest)


def make_args(**overrides) -> argparse.Namespace:
    defaults = dict(
        print_columns=False, text_col=None, audio_col=None, id_col=None,
        ignore_id_index=False, min_duration=0.5, max_duration=30.0,
        val_split_pct=5, limit=0, dry_run=False,
    )
    defaults.update(overrides)
    return argparse.Namespace(**defaults)


def write_wav(path: Path, seconds: float = 0.8, rate: int = 16000) -> None:
    """Minimal valid 16 kHz mono WAV (440 Hz sine) written via stdlib."""
    path.parent.mkdir(parents=True, exist_ok=True)
    frames = int(rate * seconds)
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        wav.writeframes(
            b"".join(struct.pack("<h", int(8000 * math.sin(2 * math.pi * 440 * i / rate)))
                     for i in range(frames))
        )


# --- column detection -------------------------------------------------------

def test_detect_columns_matches_release_variants():
    assert ingest.detect_columns(["uniq_id", "transcrip_text"]) == {
        "id": "uniq_id", "text": "transcrip_text",
    }
    assert ingest.detect_columns(["unique_id", "audio_path", "transcript"]) == {
        "id": "unique_id", "audio": "audio_path", "text": "transcript",
    }
    assert ingest.detect_columns(["uid", "wav_filepath", "sentence"]) == {
        "id": "uid", "audio": "wav_filepath", "text": "sentence",
    }


def test_detect_columns_missing_text_role():
    # No text-like column: detection yields only 'id'
    assert ingest.detect_columns(["uniq_id", "speaker"]) == {"id": "uniq_id"}


# --- audio resolution -------------------------------------------------------

def test_ingest_resolves_audio_by_id_stem_scan(tmp_path):
    """TSV without an audio column: audio found by unique_id stem scan (16k rename)."""
    lang = tmp_path / "Hindi"
    (lang / "tsv").mkdir(parents=True)
    write_wav(lang / "audio" / "hil_iv_00001_16k.wav")
    (lang / "tsv" / "meta_file.tsv").write_text(
        "uniq_id\ttranscrip_text\nhil_iv_00001\tnamaste duniya\n",
        encoding="utf-8",
    )
    out = tmp_path / "out"
    stats, coverage = __import__("collections").Counter(), __import__("collections").Counter()

    ok = ingest.ingest_language("hi", lang, out, make_args(), stats)

    assert ok is True
    manifest = json.loads((out / "manifest_hi_train.jsonl").read_text(encoding="utf-8"))
    assert manifest["text"] == "namaste duniya"
    assert "\\" not in manifest["audio_filepath"]
    assert (out / manifest["audio_filepath"]).resolve() == (lang / "audio" / "hil_iv_00001_16k.wav").resolve()


def test_ingest_explicit_audio_path_csv(tmp_path):
    """CSV with comma delimiter + explicit audio_path column resolves directly."""
    lang = tmp_path / "Kannada"
    lang.mkdir(parents=True)
    write_wav(lang / "audio" / "kn_iv_00001_16k.wav")
    (lang / "kn_transcripts.csv").write_text(
        "unique_id,audio_path,transcript\n"
        f"kn_iv_00001,Kannada/audio/kn_iv_00001_16k.wav,nanna hesaru guru\n",
        encoding="utf-8",
    )
    out = tmp_path / "out"
    stats = __import__("collections").Counter()

    ok = ingest.ingest_language("kn", lang, out, make_args(), stats)

    assert ok
    manifest = json.loads((out / "manifest_kn_train.jsonl").read_text(encoding="utf-8"))
    assert manifest["text"] == "nanna hesaru guru"
    assert "\\" not in manifest["audio_filepath"]
    assert (out / manifest["audio_filepath"]).exists()


# --- drops and diagnostics --------------------------------------------------

def test_ingest_drops_invalid_rows_with_diagnostics(tmp_path):
    lang = tmp_path / "Hindi"
    (lang / "audio").mkdir(parents=True)
    write_wav(lang / "audio" / "a_16k.wav", seconds=2.5)
    # b: empty text; c: missing audio; d: too short for min_duration=2.0
    write_wav(lang / "audio" / "d_16k.wav", seconds=0.6)
    (lang / "meta.tsv").write_text(
        "uniq_id\ttranscrip_text\n"
        "a\tpurna vakya\n"
        "b\t\n"
        "c\torphan row\n"
        "d\tbahut chhoti\n",
        encoding="utf-8",
    )
    out = tmp_path / "out"
    stats = __import__("collections").Counter()

    ingest.ingest_language("hi", lang, out, make_args(min_duration=2.0, max_duration=30.0), stats)

    manifest = json.loads((out / "manifest_hi_train.jsonl").read_text(encoding="utf-8"))
    assert manifest["text"] == "purna vakya"            # only row 'a' survives
    assert stats["hi:dropped_text"] == 1               # empty transcript
    assert stats["hi:dropped_missing_audio"] == 1      # orphan id
    assert stats["hi:dropped_bad_duration"] == 1       # 0.6 s < 2.0 s min


def test_ingest_dedups_by_uid(tmp_path):
    lang = tmp_path / "Hindi"
    (lang / "audio").mkdir(parents=True)
    write_wav(lang / "audio" / "dup1_16k.wav")
    (lang / "meta.tsv").write_text(
        "uniq_id\ttranscrip_text\ndup1\tpehli baar\ndup1\tdusri baar\n",
        encoding="utf-8",
    )
    out = tmp_path / "out"
    stats = __import__("collections").Counter()

    ingest.ingest_language("hi", lang, out, make_args(), stats)

    lines = (out / "manifest_hi_train.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert stats["hi:dropped_duplicate"] == 1


def test_corpus_shared_between_manifests(tmp_path):
    """No duplicate leakage: same uid seen again within separate TSVs is deduped."""
    lang = tmp_path / "Hindi"
    (lang / "audio").mkdir(parents=True)
    write_wav(lang / "audio" / "one_16k.wav")
    (lang / "part1.tsv").write_text("uniq_id\ttranscrip_text\none\tpart one\n", encoding="utf-8")
    (lang / "part2.tsv").write_text("uniq_id\ttranscrip_text\none\tpart two\n", encoding="utf-8")
    out = tmp_path / "out"
    stats = __import__("collections").Counter()

    ingest.ingest_language("hi", lang, out, make_args(), stats)

    assert len((out / "manifest_hi_train.jsonl").read_text(encoding="utf-8").splitlines()) == 1
    assert stats["hi:dropped_duplicate"] == 1


# --- pipeline behaviors -----------------------------------------------------

def test_dry_run_writes_nothing(tmp_path):
    lang = tmp_path / "Hindi"
    (lang / "audio").mkdir(parents=True)
    write_wav(lang / "audio" / "x_16k.wav")
    (lang / "meta.tsv").write_text("uniq_id\ttranscrip_text\nx\tkuch bhi\n", encoding="utf-8")
    out = tmp_path / "out"
    stats = __import__("collections").Counter()

    ingest.ingest_language("hi", lang, out, make_args(dry_run=True), stats)

    assert not out.exists()


def test_no_transcript_tsv_returns_false(tmp_path):
    lang = tmp_path / "Hindi"
    lang.mkdir(parents=True)
    stats = __import__("collections").Counter()

    ok = ingest.ingest_language("hi", lang, tmp_path / "out", make_args(), stats)

    assert ok is False
    assert stats["hi:skipped_no_tsv"] == 1


def test_text_column_override(tmp_path):
    """Explicit --text-col override must win over auto-detection."""
    lang = tmp_path / "Hindi"
    (lang / "audio").mkdir(parents=True)
    write_wav(lang / "audio" / "ov_16k.wav")
    # Odd column names nothing auto-detects
    (lang / "meta.tsv").write_text("uniq_id\tsentence_hi\nov\tvideshi sabd\n", encoding="utf-8")
    out = tmp_path / "out"
    stats = __import__("collections").Counter()

    ok = ingest.ingest_language("hi", lang, out, make_args(text_col="sentence_hi"), stats)

    assert ok is True
    manifest = json.loads((out / "manifest_hi_train.jsonl").read_text(encoding="utf-8"))
    assert manifest["text"] == "videshi sabd"


# --- split determinism ------------------------------------------------------

def test_split_row_deterministic_extremes():
    assert ingest.split_row("any-uid", val_split_pct=0) == "train"
    assert ingest.split_row("any-uid", val_split_pct=100) == "val"
    # Same uid → same bucket, always
    assert ingest.split_row("stable-uid", 50) == ingest.split_row("stable-uid", 50)


# --- wasm header guard ------------------------------------------------------

def test_wav_duration_corrupt_file_returns_none(tmp_path):
    bad = tmp_path / "broken.wav"
    bad.write_bytes(b"RIFF-not-really-a-wav-header" + b"\x00" * 100)
    assert ingest.wav_duration(bad) is None


def test_wav_duration_blank_wav_below_min_frames(tmp_path):
    """A near-empty WAV (8 frames ≈ 0.0005 s) fails WAV_MIN_HEADER_FRAMES=800 guard."""
    blank = tmp_path / "blank.wav"
    with wave.open(str(blank), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        w.writeframes(b"\x00" * 16)   # 8 frames
    assert ingest.wav_duration(blank) is None
