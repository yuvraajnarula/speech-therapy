#!/usr/bin/env python3
"""
Phonetics annotation pass: ingested manifests → error-annotated SFT pairs.

Takes the relative-path manifests produced by ingest_indicvoices.py
(manifest_{lang}_{split}.jsonl with {audio_filepath, text, ...}), synthesizes
clinically plausible "spoken" transcripts from each reference, and annotates
every (target, spoken) pair with the production phonetics engine
(backend.app.services.phonetics_engine.PhoneticsEngine.analyze).

Why simulate the spoken channel: IndicVoices speakers read their reference
correctly, so raw pairs carry no articulation errors. Clinical SFT pairs need
*known* error ground truth. This pass injects documented pediatric articulation
error patterns (gliding, lisp, velar fronting, voicing confusion, final
consonant deletion; Indic-script equivalents for Devanagari) with a seeded RNG,
balanced towards phonemes with the lowest coverage, then lets the real engine
produce the diagnosis (errors, phoneme strings, accuracy, clinical feedback) so
the pairs match the product's runtime behavior exactly.

Output schema (matches backend/sarvam_train.jsonl and
MLOpsPipeline.export_anonymized_sft_dataset):

    {"instruction": "...",
     "input": "Target Phrase: ...\nSpoken Phrase: ...\nTarget Phonemes: ...\nSpoken Phonemes: ...",
     "output": "<engine clinical feedback>",
     "meta": {"language": ..., "uid": ..., "error_mode": ..., "injected": [...],
              "accuracy_score": ..., "source_audio": <relative path>}}

Usage:
    python backend/scripts/annotate_pairs.py \
        --dataset-dir dataset/indicvoices \
        --output-dir dataset/sft \
        --error-rate 0.70 --correct-frac 0.30 --seed 42

Stdlib only; the engine import needs the backend package on sys.path.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from backend.app.services.phonetics_engine import phonetics_engine  # noqa: E402
from backend.app.services.phonetics_engine import PhoneticsDiagnosticEngine

INSTRUCTION = (
    "You are an expert pediatric speech-language pathologist. "
    "Analyze the patient's articulation against the target phrase, "
    "identify phoneme errors, and formulate clinical therapy guidance."
)

# --- Articulation error patterns (documented pediatric deviations) ----------
# Latin script: (pattern regex, replacement, phoneme family it perturbs)
LATIN_PATTERNS: list[tuple[str, str, str]] = [
    (r"\br", "w", "gliding_r"),            # gliding: /r/ -> /w/
    (r"\bl", "w", "gliding_l"),            # gliding: /l/ -> /w/
    (r"\bs", "th", "frontal_lisp"),        # frontal lisp: /s/ -> /θ/
    (r"\bz", "s", "devoicing"),            # devoicing: /z/ -> /s/
    (r"\bv", "b", "stopping"),             # stopping: /v/ -> /b/
    (r"\bf", "p", "stopping"),             # stopping: /f/ -> /p/
    (r"\bth", "t", "th_fronting"),         # th-fronting: /θ/ -> /t/
    (r"\bsh", "s", "depalatalization"),
    (r"\bch", "ts", "affricate_simpl"),
    (r"\bqu", "kw", "cluster_simpl"),
    (r"\bk", "t", "velar_fronting"),       # velar fronting: /k/ -> /t/
    (r"\bg", "d", "velar_fronting"),
    (r"([a-z])\1\b", r"\1", "final_cons_del"),  # final consonant deletion
]

# Devanagari script equivalents (aspiration loss, retroflex drift, glide)
DEVANAGARI_PATTERNS: list[tuple[str, str, str]] = [
    (r"ख", "क", "aspiration_loss"), (r"घ", "ग", "aspiration_loss"),
    (r"छ", "च", "aspiration_loss"), (r"झ", "ज", "aspiration_loss"),
    (r"थ", "त", "aspiration_loss"), (r"ध", "द", "aspiration_loss"),
    (r"फ", "प", "aspiration_loss"), (r"भ", "ब", "aspiration_loss"),
    (r"ष", "स", "retroflex_fronting"), (r"ट", "त", "retroflex_fronting"),
    (r"ड", "द", "retroflex_fronting"),
    (r"र", "ल", "liquid_substitution"),
]

DEVANAGARI_RE = re.compile(r"[\u0900-\u097F]")


def uid_for(record: dict[str, Any]) -> str:
    """Stable id from manifest row content."""
    digest = hashlib.sha1(
        f"{record.get('audio_filepath', '')}|{record.get('text', '')}".encode("utf-8")
    ).hexdigest()[:12]
    return f"{record.get('language', 'xx')}_{digest}"


def pick_pattern(text: str, coverage: Counter, rng: random.Random) -> Optional[tuple[str, str, str]]:
    """Choose an error pattern that matches the text, weighted by phoneme rarity."""
    patterns = DEVANAGARI_PATTERNS if DEVANAGARI_RE.search(text) else LATIN_PATTERNS
    candidates = [
        (1, p) for p in patterns
        if re.search(p[0], text)
    ]
    if not candidates:
        return None
    # Rarely-covered error types first: sort by (coverage asc, rng jitter)
    candidates.sort(key=lambda c: (coverage.get(c[1][2], 0), rng.random()))
    return candidates[0][1]


def apply_error(text: str, pattern: tuple[str, str, str], rng: random.Random) -> tuple[str, int]:
    """Apply one error pattern once (first match), returns (corrupted_text, hits)."""
    pat, sub, _fam = pattern
    match = re.search(pat, text)
    if not match:
        return text, 0
    start, end = match.span()
    corrupted = text[:start] + sub + text[end:]
    return corrupted, 1


def build_pair(              lang_dir_manifest_record: dict[str, Any], lang_code: str, split: str,
               mode: str, pattern: Optional[tuple[str, str, str]],
               spoken_override: Optional[str],
               coverage: Counter) -> dict[str, Any]:
    """Run the production analyzer on (target, spoken) and shape the SFT record."""
    target = lang_dir_manifest_record["text"].strip()
    if mode == "correct":
        spoken = spoken_override or target
        injected: list[str] = []
    else:
        assert pattern is not None and spoken_override is None
        spoken, _ = apply_error(target, pattern, random.Random())
        injected = [pattern[2]]
        coverage[pattern[2]] += 1

    diagnosis = phonetics_engine.analyze(target, spoken, language=lang_code)

    sft_record = {
        "instruction": INSTRUCTION,
        "input": (
            f"Target Phrase: {target}\n"
            f"Spoken Phrase: {spoken}\n"
            f"Target Phonemes: {diagnosis['target_phonemes']}\n"
            f"Spoken Phonemes: {diagnosis['spoken_phonemes']}"
        ),
        "output": diagnosis["clinical_feedback"],
        "meta": {
            "language": lang_code,
            "uid": uid_for(lang_dir_manifest_record),
            "split": split,
            "error_mode": mode,
            "injected": injected,
            "accuracy_score": diagnosis["accuracy_score"],
            "source_audio": lang_dir_manifest_record.get("audio_filepath", ""),
        },
    }
    return sft_record


def annotate_file(manifest_path: Path, out_dir: Path, args: argparse.Namespace,
                  stats: Counter, coverage: Counter) -> int:
    """Annotate one manifest file; returns number of SFT records written."""
    lang_match = re.match(r"manifest_([a-z\-A-Z]+)_(train|val)\.jsonl", manifest_path.name)
    if not lang_match:
        stats["skipped_unrecognized_manifest"] += 1
        return 0
    lang_code, split = lang_match.group(1), lang_match.group(2)

    records, emitted = [], 0
    rows = [json.loads(line) for line in manifest_path.read_text(encoding="utf-8").splitlines() if line.strip()]

    for row in rows:
        if args.limit_per_lang and emitted >= args.limit_per_lang:
            break
        text = (row.get("text") or "").strip()
        if not text:
            stats[f"{lang_code}:skipped_empty_text"] += 1
            continue

        uid_int = int(hashlib.sha1(uid_for(row).encode()).hexdigest()[:8], 16)
        rng = random.Random(args.seed + uid_int % 10_000)
        correct = rng.random() < args.correct_frac
        if correct:
            stats[f"{lang_code}:correct_mode"] += 1
            cov_key = "correct"
            coverage[cov_key] += 1
            records.append(build_pair(row, lang_code, split, "correct", None, None, coverage))
            emitted += 1
            continue

        pattern = pick_pattern(text, coverage, rng)
        if pattern is None:
            stats[f"{lang_code}:skipped_no_pattern_for_script"] += 1
            continue
        stats[f"{lang_code}:error_mode"] += 1
        records.append(build_pair(row, lang_code, split, "error", pattern, None, coverage))
        emitted += 1

    if args.dry_run and records:
        print(f"[{lang_code}/{split}] dry-run: would write {len(records)} pairs")
    if not args.dry_run and records:
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"phonetics_pairs_{lang_code}_{split}.jsonl"
        with open(out_path, "w", encoding="utf-8") as f:
            for record in records:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

    stats[f"{lang_code}:{split}_written"] += emitted
    return emitted


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dataset-dir", default=REPO_ROOT / "dataset" / "indicvoices", type=Path,
                        help="Directory containing manifest_{lang}_{split}.jsonl")
    parser.add_argument("--manifests", nargs="*", default=None, type=Path,
                        help="Explicit manifest file paths (overrides --dataset-dir)")
    parser.add_argument("--output-dir", default=REPO_ROOT / "dataset" / "sft", type=Path)
    parser.add_argument("--correct-frac", type=float, default=0.30,
                        help="Fraction of records kept as 'correct' (no-error) pairs")
    parser.add_argument("--error-rate", type=float, default=0.70, help="(informational; 1-correct-frac)")
    parser.add_argument("--limit-per-lang", type=int, default=0, help="Max pairs per manifest (0 = all)")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.correct_frac < 0 or args.correct_frac > 1:
        parser.error("--correct-frac must be in [0, 1]")

    manifests = (
        sorted(args.manifests)
        if args.manifests
        else sorted((args.dataset_dir).glob("manifest_*_*.jsonl"))
    )
    if not manifests:
        print("No manifests found; run ingest_indicvoices.py first.", file=sys.stderr)
        return 1

    stats: Counter = Counter()
    coverage: Counter = Counter()
    for manifest_path in manifests:
        annotate_file(manifest_path, args.output_dir, args, stats, coverage)

    summary = {
        "dry_run": args.dry_run,
        "correct_frac": args.correct_frac,
        "seed": args.seed,
        "totals": {k: v for k, v in sorted(stats.items()) if k.endswith("_written")},
        "diagnostics": {
            k: v for k, v in sorted(stats.items())
            if not k.endswith("_written") and not k.endswith("_mode")
        },
        "modes": {k: v for k, v in sorted(stats.items()) if k.endswith("_mode")},
        "error_type_coverage": {
            k: v for k, v in sorted(coverage.items())
        },
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "annotation_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary["totals"], indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
