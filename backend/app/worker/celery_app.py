"""
Celery async worker application for IndicAST Clinical Speech Therapy Platform.

Tasks:
  - export_sft_dataset_task: Background SFT dataset export (JSONL)
  - run_batch_analytics_task: Batch phoneme analytics across a session
  - cleanup_expired_audio_task: Prune audio files past retention policy
"""
import os

from celery import Celery

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "indicast_worker",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["backend.app.worker.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
    # Retry policy defaults
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    # Rate limiting for heavy ML tasks
    task_annotations={
        "backend.app.worker.tasks.export_sft_dataset_task": {"rate_limit": "5/m"},
        "backend.app.worker.tasks.run_batch_analytics_task": {"rate_limit": "20/m"},
    },
    # Result expiry: 1 hour
    result_expires=3600,
    # Beat schedule (periodic tasks)
    beat_schedule={
        "cleanup-expired-audio-daily": {
            "task": "backend.app.worker.tasks.cleanup_expired_audio_task",
            "schedule": 86400.0,  # every 24 hours
        },
    },
)
