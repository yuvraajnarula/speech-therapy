import os
from typing import Dict, List, Optional
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

    # Enterprise Identity Provider (OIDC / OAuth2 / JWKS)
    # Comma-separated list of provider names enabled (e.g. "auth0,cognito,firebase,google,azure")
    OIDC_ENABLED_PROVIDERS: str = ""
    # Per-provider JWKS URLs (JSON dict: {"auth0": "https://.../.well-known/jwks.json"})
    OIDC_JWKS_URLS: str = "{}"
    # Per-provider client IDs (JSON dict: {"auth0": "client_id"})
    OIDC_CLIENT_IDS: str = "{}"
    # Per-provider issuers (JSON dict: {"auth0": "https://.../"})
    OIDC_ISSUERS: str = "{}"
    # Email domains allowed to self-identify as clinicians (comma-separated)
    CLINICIAN_EMAIL_DOMAINS: str = ""

    # CORS — comma-separated origin allow-list (no wildcards in production)
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173"

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


def _parse_json_dict(value: str) -> Dict[str, str]:
    """Parse a JSON string into a dict, returning {} on failure."""
    import json
    try:
        data = json.loads(value)
        if isinstance(data, dict):
            return {str(k): str(v) for k, v in data.items()}
    except Exception:
        pass
    return {}


def _parse_csv_list(value: str) -> List[str]:
    """Parse a comma-separated string into a list of stripped values."""
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


# ---------------------------------------------------------------------------
# Module-level OIDC helper accessors.
# Pydantic v2 forbids attaching arbitrary attributes to a Settings instance,
# so these are exposed as plain functions instead of `settings.*` attributes.
# ---------------------------------------------------------------------------

def get_oidc_jwks_url(provider: str) -> Optional[str]:
    """Return the JWKS URL for the given provider, or None if not configured."""
    return _parse_json_dict(settings.OIDC_JWKS_URLS).get(provider)


def get_oidc_client_id(provider: str) -> Optional[str]:
    """Return the client ID for the given provider, or None if not configured."""
    return _parse_json_dict(settings.OIDC_CLIENT_IDS).get(provider)


def get_oidc_issuer(provider: str) -> Optional[str]:
    """Return the issuer URL for the given provider, or None if not configured."""
    return _parse_json_dict(settings.OIDC_ISSUERS).get(provider)


def oidc_enabled_providers() -> List[str]:
    """List of enabled enterprise identity providers."""
    return _parse_csv_list(settings.OIDC_ENABLED_PROVIDERS)


def clinician_email_domains() -> List[str]:
    """Email domains allowed to self-identify as clinicians."""
    return _parse_csv_list(settings.CLINICIAN_EMAIL_DOMAINS)
