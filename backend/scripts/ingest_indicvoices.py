#!/usr/bin/env python3
"""
IndicVoices → IndicAST dataset ingestion.

Converts a locally downloaded / extracted IndicVoices tree (AI4Bharat, 22 Indian
languages, 16 kHz mono WAV) into the platform's canonical training manifest
schema used by whisper_train_fixed.jsonl and the SFT exports:

    {"audio_filepath": <path RELATIVE to the output directory>,
     "text": <verbatim transcript>,
     "duration": <seconds>, "language": <iso-ish code>, "source": "indicvoices"}

Why relative paths: the old manifests baked absolute Windows paths
("D:\\code\\...\\audio_123.wav"), which break on every other machine. Audio
files themselves are gitignored (*.wav), so the repo carries only manifests +
summary — reproducing the dataset only needs the source dir.

IndicVoices released layout (per https://github.com/AI4Bharat/IndicVoices):

    SOURCE_DIR
    ├── Hindi/          ├── Kannada/      ├── Tamil/        ├── Telugu/
    │   ├── meta file / transcript TSVs (columns vary per release)
    │   └── *.wav       (audio; 16 kHz downsamples keep a `_16k` suffix)

Transcript metadata columns are NOT globally stable across releases, so this
script auto-detects id / audio-path / text columns and allows --print-columns /
--id-col / --audio-col / --text-col overrides.

Usage (from repo root):
    python backend/scripts/ingest_indicvoices.py \
        --source D:/datasets/IndicVoices \
        --languages hi kn ta te \
        --output-dir dataset/indicvoices \
        --limit 5000        # per language, optional
        --dry-run           # scan + report without writing

Outputs:
    dataset/indicvoices/manifest_{lang}_train.jsonl   (~95%)
    dataset/indicvoices/manifest_{lang}_val.jsonl     (~5%, deterministic split)
    dataset/indicvoices/ingest_summary.json

Stdlib only — no pandas, no numpy: IndicVoices stays a data step, not a dependency.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import sys
import wave
from collections import Counter
from pathlib import Path
from typing import Any, Optional

REPO_ROOT = Path(__file__).resolve().parents[2]

# IndicVoices release folders → platform dialect codes (the 22 Eighth Schedule
# languages; the therapy tracks pick the first four).
LANGUAGE_FOLDER_MAP: dict[str, str] = {
    "Hindi": "hi", "Kannada": "kn", "Tamil": "ta", "Telugu": "te", "Malayalam": "ml",
    "Marathi": "mr", "Bengali": "bn", "Gujarati": "gu", "Punjabi": "pa", "Odia": "or",
    "Assamese": "as", "Nepali": "ne", "Urdu": "ur", "Sanskrit": "sa",
    "Santali": "sat", "Sindhi": "sd", "Manipuri": "mni", "Bodo": "brx",
    "Dogri": "doi", "Kashmiri": "kas", "Konkani": "gom", "Maithili": "mai",
    "English": "en-In",
}

# Column auto-detection: (role, ordered regex candidates). First match wins.
COLUMN_CANDIDATES: list[tuple[str, tuple[str, ...]]] = [
    ("id", (r"^uniq[ _-]?id$", r"^unique[ _-]?id$", r"^uid$", r"^id$")),
    ("audio", (
        r"^audio[ _-]?filepath$", r"^wav[ _-]?filepath$", r"^audio[ _-]?path$",
        r"^wav[ _-]?path$", r"^audio[ _-]?file(name)?$", r"^wav[ _-]?file(name)?$",
        r"^file[ _-]?path$", r"^path$",
    )),
    ("text", (
        r"^transcrip.*", r"^transcription.*", r"^transcript.*", r"^text$", r"^sentence$",
    )),
]

MAX_TEXT_LEN = 512           # chars; prompts should not be novels
WAV_MIN_HEADER_FRAMES = 800   # 0.05 s @16 kHz — rejects corrupt/empty files


def detect_columns(header: list[str], overrides: Optional[dict[str, str]] = None) -> dict[str, str]:
    """Map each role (id/audio/text) to the first matching header cell.

    Explicit --text-col/--audio-col/--id-col overrides are tried after the
    built-in regexes and win (they append an exact-match pattern).
    """
    found: dict[str, str] = {}
    for role, patterns in COLUMN_CANDIDATES:
        extra = tuple() 
        if overrides and overrides.get(role):
            extra = (f"^{re.escape(overrides[role])}$",)
        for pat in tuple(patterns) + extra:
            for cell in header:
                if re.match(pat, cell.strip().lower(), flags=re.IGNORECASE) and role not in found:
                    found[role] = cell
    return found


def read_tsv(path: Path) -> Optional[tuple[list[str], list[list[str]]]]:
    """Read a transcript TSV whose delimiter is tab or comma (tab first)."""
    for delimiter in ("\t", ","):
        try:
            with open(path, newline="", encoding="utf-8-sig") as f:
                rows = list(csv.reader(f, delimiter=delimiter))
        except UnicodeDecodeError:
            continue
        if not rows or len(rows[0]) < 2:
            continue
        return rows[0], rows[1:]
    return None


def clean_text(raw: str) -> str:
    """Collapse whitespace; drops rows that reduce to noise."""
    return re.sub(r"\s+", " ", (raw or "")).strip()


def wav_duration(path: Path) -> Optional[float]:
    """Read the WAV header for validity + duration in seconds. None = unusable file."""
    try:
        with wave.open(str(path), "rb") as wav:
            frames, rate = wav.getnframes(), wav.getframerate()
    except (EOFError, wave.Error, OSError):
        return None
    if rate <= 0 or frames < WAV_MIN_HEADER_FRAMES:
        return None
    return round(frames / rate, 3)


class AudioIndex:
    """
    unique_id → wav path, built once per language by scanning filenames.
    Handles the 16 kHz rename pattern (_16k suffix) via stem matching.
    """

    def __init__(self, root: Path):
        self._by_stem: dict[str, list[Path]] = {}
        for wav_file in root.rglob("*.wav"):
            stem = re.sub(r"[_-]16k$", "", wav_file.stem.lower())
            self._by_stem.setdefault(stem, []).append(wav_file)
        for stem in self._by_stem:
            self._by_stem[stem].sort(key=lambda p: p.stat().st_size, reverse=True)

    def lookup(self, uid: str) -> Optional[Path]:
        return (self._by_stem.get(uid.strip().lower(), []) or [None])[0]


def normalize_audio_path(raw: str, tsv_dir: Path) -> Optional[Path]:
    """Resolve a TSV audio-path cell to a real file near the TSV or up the tree."""
    if not raw or str(raw).lower() in ("nan", "none", "<path>"):
        return None
    candidate = Path(raw)
    if candidate.is_absolute() and candidate.exists():
        return candidate
    for base in (tsv_dir, *tsv_dir.parents[:4]):
        resolved = base / candidate.name      # audio commonly travels flat next to TSVs
        if resolved.exists():
            return resolved
        resolved = base / candidate
        if resolved.exists():
            return resolved
    return None


def split_row(uid: str, val_split_pct: int) -> str:
    """Deterministic split: hash of the utterance id → 'train' | 'val'."""
    digest = hashlib.sha256(uid.encode("utf-8")).hexdigest()
    return "val" if int(digest[:8], 16) % 100 < val_split_pct else "train"


def ingest_language(code: str, lang_dir: Path, out_dir: Path, args: argparse.Namespace,
                    stats: Counter) -> bool:
    """
    Ingest one language folder (all transcript TSVs + audio scan inside it).
    Returns True if any manifest-ready records were produced.
    """
    tsvs = sorted(p for p in lang_dir.rglob("*.tsv")) + sorted(p for p in lang_dir.rglob("*.csv"))
    if not tsvs:
        print(f"[{code}] no transcript metadata (.tsv/.csv) under {lang_dir}; skipped", file=sys.stderr)
        stats[f"{code}:skipped_no_tsv"] += 1
        return False

    records: dict[str, dict[str, Any]] = {}    # uid → record (dedupe by uid)
    understood = False

    overrides = {role: getattr(args, f"{role}_col", None) for role in ("id", "audio", "text")}
    for tsv in tsvs:
        parsed = read_tsv(tsv)
        if parsed is None:
            continue
        header, rows = parsed
        cols = detect_columns(header, overrides)

        if args.print_columns:
            print(f"[{code}] {tsv.name}: header={header[:10]} detected={cols}")
        if "text" not in cols:
            stats[f"{code}:tsv_without_text_column"] += 1
            continue
        understood = True

        audio_index = AudioIndex(lang_dir)
        tsv_dir = tsv.parent

        for raw_row in rows:
            if len(raw_row) < len(header):
                continue
            row = dict(zip(header, raw_row))
            text = clean_text(row.get(cols.get("text", ""), ""))
            if not text or len(text) > MAX_TEXT_LEN:
                stats[f"{code}:dropped_text"] += 1
                continue

            uid = (row.get(cols.get("id", ""), "") or "").strip()

            # --- resolve audio: TSV path column, else unique_id stem scan -------
            wav: Optional[Path] = None
            if "audio" in cols:
                wav = normalize_audio_path(row[cols["audio"]], tsv_dir)
            if wav is None and not args.ignore_id_index:
                wav = audio_index.lookup(uid or text[:24])
            if wav is None or not wav.exists():
                stats[f"{code}:dropped_missing_audio"] += 1
                continue

            uid = uid or wav.stem           # dedupe key fallback
            duration = wav_duration(wav)
            if duration is None or not (args.min_duration <= duration <= args.max_duration):
                stats[f"{code}:dropped_bad_duration"] += 1
                continue
            if uid in records:
                stats[f"{code}:dropped_duplicate"] += 1
                continue
            if args.limit and len(records) >= args.limit:
                break

            records[uid] = {
                "audio_filepath": os.path.relpath(wav, out_dir).replace("\\", "/"),
                "text": text,
                "duration": duration,
                "language": code,
                "source": "indicvoices",
            }

    if not understood:
        print(f"[{code}] transcript TSVs found but no text column matched; "
              "use --print-columns and --text-col to override", file=sys.stderr)
        stats[f"{code}:skipped_no_text_col"] += 1
        return False

    # --- split + write manifests ---------------------------------------------
    buckets: dict[str, list[dict[str, Any]]] = {"train": [], "val": []}
    for uid, record in records.items():
        buckets[split_row(uid, args.val_split_pct)].append(record)

    total_hours = sum(r["duration"] for r in records.values()) / 3600.0
    if not args.dry_run:
        out_dir.mkdir(parents=True, exist_ok=True)
        for split, split_rows in buckets.items():
            if not split_rows:
                continue
            out_path = out_dir / f"manifest_{code}_{split}.jsonl"
            with open(out_path, "w", encoding="utf-8") as f:
                for record in split_rows:
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")
            stats[f"{code}:{split}_written"] += len(split_rows)
    print(f"[{code}] records={len(records)} hours={total_hours:.2f} "
          f"train={len(buckets['train'])} val={len(buckets['val'])}")

    stats[f"{code}:hours"] = round(stats[f"{code}:hours"] + total_hours, 3)
    stats[f"{code}:records"] += len(records)
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--source", required=True, type=Path,
                        help="IndicVoices extraction root (Hindi/, Kannada/, ... folders)")
    parser.add_argument("--output-dir", default=REPO_ROOT / "dataset" / "indicvoices", type=Path)
    parser.add_argument("--languages", nargs="*", default=["hi", "kn", "ta", "te"],
                        help="Dialect codes (see LANGUAGE_FOLDER_MAP)")
    parser.add_argument("--min-duration", type=float, default=0.5)
    parser.add_argument("--max-duration", type=float, default=30.0)
    parser.add_argument("--val-split-pct", type=int, default=5)
    parser.add_argument("--limit", type=int, default=0, help="Max records per language (0 = all)")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--print-columns", action="store_true", help="Dump TSV headers + detection")
    parser.add_argument("--ignore-id-index", action="store_true",
                        help="Never guess audio by unique_id file-stem scan")
    parser.add_argument("--text-col", type=str, help="Force transcript column name")
    parser.add_argument("--audio-col", type=str, help="Force audio path column name")
    parser.add_argument("--id-col", type=str, help="Force id column name")
    args = parser.parse_args()

    if not args.source.exists():
        parser.error(f"--source does not exist: {args.source}")

    # Language folder may carry release suffixes (e.g. 'Hindi-v2'); prefix match.
    folder_for_code: dict[str, Path] = {}
    for entry in sorted(p for p in args.source.iterdir() if p.is_dir()):
        for folder, code in LANGUAGE_FOLDER_MAP.items():
            if entry.name.lower().startswith(folder.lower()):
                folder_for_code.setdefault(code, entry)

    stats: Counter = Counter()
    ingested_any = False
    for code in args.languages:
        lang_dir = folder_for_code.get(code)
        if lang_dir is None:
            print(f"[{code}] folder not found under {args.source}; skipped", file=sys.stderr)
            stats[f"{code}:skipped_missing_folder"] += 1
            continue
        ingested_any = ingest_language(code, lang_dir, args.output_dir, args, stats) or ingested_any

    summary = {
        "source": str(args.source),
        "dry_run": args.dry_run,
        "totals": {},
        "diagnostics": {k: v for k, v in sorted(stats.items()) if not k.endswith(":hours")},
    }
    for code in args.languages:
        if stats.get(f"{code}:records", 0):
            summary["totals"][code] = {
                "records": stats[f"{code}:records"],
                "hours": stats.get(f"{code}:hours", 0.0),
            }
    if not args.dry_run:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        (args.output_dir / "ingest_summary.json").write_text(
            json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    if not ingested_any:
        print("\nNothing ingested: no language folder yielded valid records.", file=sys.stderr)
        print("Re-run with --print-columns and pass --text-col/--audio-col/--id-col overrides.",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
