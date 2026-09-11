import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    PROJECT_NAME: str = "Enterprise Speech Therapy MBP"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"

    # Security & Auth
    SECRET_KEY: str = "enterprise-super-secret-key-change-in-production-min32bytes!"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./speech_therapy.db"

    # Storage
    STORAGE_BACKEND: str = "local"  # "local", "s3", or "gcs"
    LOCAL_STORAGE_DIR: str = "./dataset/audio_store"
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "us-east-1"
    S3_BUCKET_NAME: str = "speech-therapy-clinical-audio"
    S3_ENDPOINT_URL: Optional[str] = None

    # HIPAA / Healthcare Compliance
    ENABLE_HIPAA_LOG_REDACTION: bool = True
    ENCRYPT_AUDIO_AT_REST: bool = True
    DATASET_EXPORT_DIR: str = "./dataset/anonymized_exports"

    # AI & AST Models
    DEFAULT_STT_MODEL: str = "small"
    STT_DEVICE: str = "cpu"
    STT_COMPUTE_TYPE: str = "int8"
    ENABLE_INDIC_AST: bool = True
    DEFAULT_SOURCE_LANGUAGE: str = "hi"
    DEFAULT_TARGET_LANGUAGE: str = "en"

    # MLOps
    MLOPS_TRACKER: str = "local"  # "local", "wandb", "mlflow"
    WANDB_API_KEY: Optional[str] = None
    WANDB_PROJECT: str = "speech-therapy-ast"
    MLFLOW_TRACKING_URI: Optional[str] = None


settings = Settings()
