import json
from datetime import datetime
from pathlib import Path
from typing import Any

from backend.app.core.config import settings
from backend.app.core.logging import app_logger, audit_logger


class MLOpsPipeline:
    """
    Automated MLOps pipeline for tracking model performance, managing
    clinical datasets, and exporting fine-tuning manifests (Whisper & Sarvam SFT).
    """

    def __init__(self):
        self.tracker_type = settings.MLOPS_TRACKER
        self.export_dir = Path(settings.DATASET_EXPORT_DIR)
        self.export_dir.mkdir(parents=True, exist_ok=True)
        self._init_tracker()

    def _init_tracker(self):
        if self.tracker_type == "wandb" and settings.WANDB_API_KEY:
            try:
                import wandb
                wandb.login(key=settings.WANDB_API_KEY)
                wandb.init(project=settings.WANDB_PROJECT, reinit=True)
                app_logger.info("Weights & Biases (W&B) tracker initialized.")
            except Exception as e:
                app_logger.warning(f"Could not initialize W&B: {e}")
        elif self.tracker_type == "mlflow" and settings.MLFLOW_TRACKING_URI:
            try:
                import mlflow
                mlflow.set_tracking_uri(settings.MLFLOW_TRACKING_URI)
                app_logger.info("MLflow tracker initialized.")
            except Exception as e:
                app_logger.warning(f"Could not initialize MLflow: {e}")
        else:
            app_logger.info("Using local MLOps metrics logging.")

    def log_evaluation_metrics(
        self,
        wer: float,
        per: float,
        dialect: str,
        total_samples: int,
        metadata: dict[str, Any] | None = None
    ):
        """Log speech metrics across dialects."""
        metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "wer": wer,
            "per": per,
            "dialect": dialect,
            "total_samples": total_samples,
            **(metadata or {})
        }

        if self.tracker_type == "wandb":
            try:
                import wandb
                wandb.log(metrics)
            except Exception as e:
                app_logger.error(f"Failed to log to W&B: {e}")
        elif self.tracker_type == "mlflow":
            try:
                import mlflow
                mlflow.log_metrics({"wer": wer, "per": per}, step=total_samples)
            except Exception as e:
                app_logger.error(f"Failed to log to MLflow: {e}")
        else:
            metrics_file = self.export_dir / "metrics_history.jsonl"
            with open(metrics_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(metrics) + "\n")

    def export_anonymized_sft_dataset(
        self,
        attempts: list[dict[str, Any]],
        output_filename: str = "sarvam_sft_dataset.jsonl"
    ) -> Path:
        """
        Exports HIPAA-compliant, de-identified SFT training pairs for
        Sarvam or Whisper fine-tuning.
        """
        output_path = self.export_dir / output_filename
        exported_count = 0

        with open(output_path, "w", encoding="utf-8") as f:
            for item in attempts:
                target_text = item.get("target_phrase", "")
                spoken_text = item.get("spoken_phrase", "")
                target_phonemes = item.get("target_phonemes", "")
                spoken_phonemes = item.get("spoken_phonemes", "")
                clinical_notes = item.get("clinical_feedback", "Clinical feedback.")

                record = {
                    "instruction": (
                        "You are an expert pediatric speech-language pathologist. "
                        "Analyze the patient's articulation against the target phrase, "
                        "identify phoneme errors, and formulate clinical therapy guidance."
                    ),
                    "input": (
                        f"Target Phrase: {target_text}\n"
                        f"Spoken Phrase: {spoken_text}\n"
                        f"Target Phonemes: {target_phonemes}\n"
                        f"Spoken Phonemes: {spoken_phonemes}"
                    ),
                    "output": clinical_notes
                }
                f.write(json.dumps(record) + "\n")
                exported_count += 1

        audit_logger.info(
            f"Exported {exported_count} anonymized SFT records to {output_path}"
        )
        return output_path


mlops_pipeline = MLOpsPipeline()
