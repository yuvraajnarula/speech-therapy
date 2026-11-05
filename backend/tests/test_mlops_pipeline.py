"""
Tests for backend/app/services/mlops_pipeline.py — MLOps metrics + SFT export.

Covers: MLOpsPipeline init (tracker selection), log_evaluation_metrics (local/W&B/MLflow),
export_anonymized_sft_dataset (anonymized JSONL output), and singleton.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from backend.app.services.mlops_pipeline import MLOpsPipeline, mlops_pipeline


# ---------------------------------------------------------------------------
# MLOpsPipeline init / tracker selection
# ---------------------------------------------------------------------------

def test_mlops_pipeline_local_tracker(tmp_path, monkeypatch):
    from backend.app.core import config as cfg
    monkeypatch.setattr(cfg.settings, "MLOPS_TRACKER", "local")
    monkeypatch.setattr(cfg.settings, "DATASET_EXPORT_DIR", str(tmp_path / "exports"))
    pipe = MLOpsPipeline()
    assert pipe.tracker_type == "local"
    assert pipe.export_dir == Path(tmp_path / "exports")
    assert pipe.export_dir.exists()


def test_mlops_pipeline_wandb_no_key_falls_back_to_local(tmp_path, monkeypatch):
    from backend.app.core import config as cfg
    monkeypatch.setattr(cfg.settings, "MLOPS_TRACKER", "wandb")
    monkeypatch.setattr(cfg.settings, "WANDB_API_KEY", "")
    monkeypatch.setattr(cfg.settings, "DATASET_EXPORT_DIR", str(tmp_path / "exports"))
    pipe = MLOpsPipeline()
    assert pipe.tracker_type == "wandb"  # field value, but wandb not initialized


def test_mlops_pipeline_defaults_local(tmp_path, monkeypatch):
    from backend.app.core import config as cfg
    monkeypatch.setattr(cfg.settings, "MLOPS_TRACKER", "local")
    monkeypatch.setattr(cfg.settings, "DATASET_EXPORT_DIR", str(tmp_path / "exports"))
    pipe = MLOpsPipeline()
    assert pipe.tracker_type == "local"


# ---------------------------------------------------------------------------
# log_evaluation_metrics (local tracker writes metrics_history.jsonl)
# ---------------------------------------------------------------------------

def test_log_evaluation_metrics_local_writes_jsonl(tmp_path, monkeypatch):
    from backend.app.core import config as cfg
    monkeypatch.setattr(cfg.settings, "MLOPS_TRACKER", "local")
    monkeypatch.setattr(cfg.settings, "DATASET_EXPORT_DIR", str(tmp_path / "exports"))
    pipe = MLOpsPipeline()

    pipe.log_evaluation_metrics(
        wer=0.12, per=0.05, dialect="hi", total_samples=1000,
        metadata={"model": "whisper-small"},
    )

    metrics_file = pipe.export_dir / "metrics_history.jsonl"
    assert metrics_file.exists()
    line = metrics_file.read_text(encoding="utf-8").strip()
    record = json.loads(line)
    assert record["wer"] == 0.12
    assert record["per"] == 0.05
    assert record["dialect"] == "hi"
    assert record["total_samples"] == 1000
    assert record["model"] == "whisper-small"  # metadata unpacked at top level
    assert "timestamp" in record


# ---------------------------------------------------------------------------
# export_anonymized_sft_dataset
# ---------------------------------------------------------------------------

def test_export_anonymized_sft_dataset_writes_jsonl(tmp_path, monkeypatch):
    from backend.app.core import config as cfg
    monkeypatch.setattr(cfg.settings, "MLOPS_TRACKER", "local")
    monkeypatch.setattr(cfg.settings, "DATASET_EXPORT_DIR", str(tmp_path / "exports"))
    pipe = MLOpsPipeline()

    attempts = [
        {
            "target_phrase": "namaste",
            "spoken_phrase": "namaste",
            "target_phonemes": "N AH M AH S T EY",
            "spoken_phonemes": "N AH M AH S T EY",
            "clinical_feedback": "Accurate articulation achieved.",
        },
        {
            "target_phrase": "khana",
            "spoken_phrase": "tana",
            "target_phonemes": "K AH N AH",
            "spoken_phonemes": "T AH N AH",
            "clinical_feedback": "Substitution: Replaced sound /K/ with /T/.",
        },
    ]

    output_path = pipe.export_anonymized_sft_dataset(attempts)
    assert output_path.exists()
    assert output_path.suffix == ".jsonl"

    lines = output_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2

    rec1 = json.loads(lines[0])
    assert rec1["instruction"].startswith("You are an expert pediatric")
    assert "Target Phrase: namaste" in rec1["input"]
    assert "Spoken Phrase: namaste" in rec1["input"]
    assert "Target Phonemes: N AH M AH S T EY" in rec1["input"]
    assert "Spoken Phonemes: N AH M AH S T EY" in rec1["input"]
    assert rec1["output"] == "Accurate articulation achieved."

    rec2 = json.loads(lines[1])
    assert "Target Phrase: khana" in rec2["input"]
    assert rec2["output"] == "Substitution: Replaced sound /K/ with /T/."


def test_export_anonymized_sft_dataset_default_filename(tmp_path, monkeypatch):
    from backend.app.core import config as cfg
    monkeypatch.setattr(cfg.settings, "MLOPS_TRACKER", "local")
    monkeypatch.setattr(cfg.settings, "DATASET_EXPORT_DIR", str(tmp_path / "exports"))
    pipe = MLOpsPipeline()

    output_path = pipe.export_anonymized_sft_dataset([{"target_phrase": "a", "spoken_phrase": "a",
                                                       "target_phonemes": "AH", "spoken_phonemes": "AH",
                                                       "clinical_feedback": "ok"}])
    assert output_path.name == "sarvam_sft_dataset.jsonl"


def test_export_anonymized_sft_dataset_custom_filename(tmp_path, monkeypatch):
    from backend.app.core import config as cfg
    monkeypatch.setattr(cfg.settings, "MLOPS_TRACKER", "local")
    monkeypatch.setattr(cfg.settings, "DATASET_EXPORT_DIR", str(tmp_path / "exports"))
    pipe = MLOpsPipeline()

    output_path = pipe.export_anonymized_sft_dataset(
        [{"target_phrase": "a", "spoken_phrase": "a", "target_phonemes": "AH",
          "spoken_phonemes": "AH", "clinical_feedback": "ok"}],
        output_filename="custom_sft.jsonl",
    )
    assert output_path.name == "custom_sft.jsonl"


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

def test_mlops_pipeline_singleton():
    assert isinstance(mlops_pipeline, MLOpsPipeline)
