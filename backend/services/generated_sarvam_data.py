#!/usr/bin/env python3
"""
generate_sarvam_data.py — Sarvam SFT dataset generation.

Consumes the phonetic SFT pairs emitted by annotate_pairs.py
(dataset/sft/phonetics_pairs_{lang}_{split}.jsonl) and renders them into the
canonical Sarvam instruction-tuning schema used by sarvam_train.jsonl:

    {"instruction": "...", "input": "...", "output": "..."}

The per-pair "meta" block (language, uid, error_mode, injected, accuracy_score,
source_audio, ...) is dropped from the training record but surfaced in the run
summary so you can audit coverage per dialect / error mode.

Usage (from repo root):
    python backend/services/generated_sarvam_data.py \
        --input-dir dataset/sft \
        --output backend/sarvam_train.jsonl \
        --error-mode error          # only error-mode pairs (default: all)
        --language en-In            # only one dialect (default: all)
        --dedup-key input           # dedupe records by input text (default: input)
        --limit 5000                # cap records (0 = all)
        --dry-run                   # scan + report without writing

Stdlib only — mirrors the style of ingest_indicvoices.py / annotate_pairs.py.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Optional

REPO_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_INSTRUCTION = (
    "You are an expert pediatric speech therapist. Analyze the child's spoken "
    "phrase against the target phrase. Identify phonetic errors "
    "(insertions, deletions, substitutions) and provide actionable therapy "
    "feedback."
)


def iter_pair_files(input_dir: Path) -> list[Path]:
    """Return sorted phonetics-pair JSONL files under input_dir."""
    return sorted(input_dir.glob("phonetics_pairs_*.jsonl"))


def read_pairs(path: Path) -> list[dict[str, Any]]:
    """Read all JSONL records from a pair file."""
    rows: list[dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def sarvam_record(pair: dict[str, Any]) -> dict[str, str]:
    """Map one annotated pair to the Sarvam training schema (no meta block)."""
    return {
        "instruction": pair.get("instruction", DEFAULT_INSTRUCTION),
        "input": pair.get("input", ""),
        "output": pair.get("output", ""),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate sarvam_train.jsonl from annotated phonetic SFT pairs."
    )
    parser.add_argument(
        "--input-dir",
        default=REPO_ROOT / "dataset" / "sft",
        type=Path,
        help="Directory containing phonetics_pairs_{lang}_{split}.jsonl",
    )
    parser.add_argument(
        "--output",
        default=REPO_ROOT / "backend" / "sarvam_train.jsonl",
        type=Path,
        help="Path to write the Sarvam SFT JSONL training file.",
    )
    parser.add_argument(
        "--error-mode",
        choices=["error", "correct", "all"],
        default="all",
        help="Filter pairs by error_mode (default: all).",
    )
    parser.add_argument(
        "--language",
        default=None,
        help="Only include pairs whose meta.language matches this dialect.",
    )
    parser.add_argument(
        "--dedup-key",
        default="input",
        help="Record field to dedupe by (default: input). Set 'none' to disable.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Max records to write (0 = all).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Scan + report without writing anything.",
    )
    args = parser.parse_args()

    if not args.input_dir.exists():
        print(f"Input dir not found: {args.input_dir}", file=sys.stderr)
        print("Run annotate_pairs.py first to produce phonetics_pairs_*.jsonl.", file=sys.stderr)
        return 1

    pair_files = iter_pair_files(args.input_dir)
    if not pair_files:
        print(f"No phonetics_pairs_*.jsonl found under {args.input_dir}", file=sys.stderr)
        print("Run annotate_pairs.py first.", file=sys.stderr)
        return 1

    stats: Counter = Counter()
    coverage: Counter = Counter()
    written: list[dict[str, str]] = []
    seen: set[str] = set()

    for pair_file in pair_files:
        pairs = read_pairs(pair_file)
        stats["files_scanned"] += 1
        stats["pairs_seen"] += len(pairs)

        for pair in pairs:
            meta = pair.get("meta", {}) or {}
            mode = meta.get("error_mode", "unknown")
            lang = meta.get("language", "xx")
            injected = meta.get("injected", []) or []

            stats[f"mode:{mode}"] += 1
            stats[f"lang:{lang}"] += 1
            for fam in injected:
                coverage[fam] += 1

            if args.error_mode != "all" and mode != args.error_mode:
                stats[f"skipped:mode_filter_{mode}"] += 1
                continue
            if args.language is not None and lang != args.language:
                stats[f"skipped:lang_filter_{lang}"] += 1
                continue

            key_field = None if args.dedup_key == "none" else args.dedup_key
            if key_field is not None:
                dedup_val = pair.get(key_field, "")
                if dedup_val in seen:
                    stats[f"skipped:dup_{key_field}"] += 1
                    continue
                seen.add(dedup_val)

            record = sarvam_record(pair)
            written.append(record)
            stats["records_selected"] += 1

            if args.limit and len(written) >= args.limit:
                break

        if args.limit and len(written) >= args.limit:
            break

    print(f"Files scanned     : {stats['files_scanned']}")
    print(f"Pairs seen        : {stats['pairs_seen']}")
    print(f"Records selected  : {stats['records_selected']}")
    if stats["records_selected"]:
        print(f"By error mode     : " + ", ".join(
            f"{k.split(':',1)[1]}={v}" for k, v in sorted(stats.items()) if k.startswith("mode:")
        ))
        print(f"By language       : " + ", ".join(
            f"{k.split(':',1)[1]}={v}" for k, v in sorted(stats.items()) if k.startswith("lang:")
        ))
    if coverage:
        print(f"Error coverage    : " + ", ".join(
            f"{k}={v}" for k, v in sorted(coverage.items())
        ))
    print(f"Skipped (dups)    : {stats.get('skipped:dup_input', 0)}")

    if args.dry_run:
        print("Dry run: nothing written.")
        return 0

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        for record in written:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"Wrote {len(written)} records to {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
