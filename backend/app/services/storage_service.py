import hashlib
from pathlib import Path

from backend.app.core.config import settings
from backend.app.core.logging import app_logger, audit_logger


class BaseStorageService:
    def upload_audio_bytes(self, audio_bytes: bytes, filename_prefix: str = "session") -> str:
        raise NotImplementedError

    def get_audio_bytes(self, storage_key: str) -> bytes:
        raise NotImplementedError

    def delete_audio(self, storage_key: str) -> bool:
        raise NotImplementedError


class LocalStorageService(BaseStorageService):
    def __init__(self, base_dir: str = settings.LOCAL_STORAGE_DIR):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _get_anonymized_path(self, audio_bytes: bytes, prefix: str) -> tuple[Path, str]:
        # Hash contents for HIPAA-safe de-identified storage
        sha256 = hashlib.sha256(audio_bytes).hexdigest()[:16]
        filename = f"{prefix}_{sha256}.wav"
        return self.base_dir / filename, filename

    def upload_audio_bytes(self, audio_bytes: bytes, filename_prefix: str = "session") -> str:
        target_path, filename = self._get_anonymized_path(audio_bytes, filename_prefix)
        target_path.write_bytes(audio_bytes)
        audit_logger.info(f"Saved audio asset locally: {filename} ({len(audio_bytes)} bytes)")
        return str(target_path.resolve())

    def get_audio_bytes(self, storage_key: str) -> bytes:
        path = Path(storage_key)
        if not path.exists():
            raise FileNotFoundError(f"Audio file not found: {storage_key}")
        return path.read_bytes()

    def delete_audio(self, storage_key: str) -> bool:
        path = Path(storage_key)
        if path.exists():
            path.unlink()
            audit_logger.info(f"Deleted audio asset: {storage_key}")
            return True
        return False


class S3StorageService(BaseStorageService):
    def __init__(self):
        import boto3
        from botocore.client import Config

        session_kwargs = {}
        if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
            session_kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
            session_kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY
        if settings.AWS_REGION:
            session_kwargs["region_name"] = settings.AWS_REGION

        client_kwargs = {}
        if settings.S3_ENDPOINT_URL:
            client_kwargs["endpoint_url"] = settings.S3_ENDPOINT_URL
            client_kwargs["config"] = Config(s3={"addressing_style": "path"})

        self.s3_client = boto3.client("s3", **session_kwargs, **client_kwargs)
        self.bucket = settings.S3_BUCKET_NAME

    def upload_audio_bytes(self, audio_bytes: bytes, filename_prefix: str = "session") -> str:
        sha256 = hashlib.sha256(audio_bytes).hexdigest()[:16]
        key = f"audio/{filename_prefix}_{sha256}.wav"

        extra_args = {}
        if settings.ENCRYPT_AUDIO_AT_REST:
            extra_args["ServerSideEncryption"] = "AES256"

        self.s3_client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=audio_bytes,
            ContentType="audio/wav",
            **extra_args,
        )
        audit_logger.info(f"Uploaded audio to S3 bucket {self.bucket}: key={key}")
        return key

    def get_audio_bytes(self, storage_key: str) -> bytes:
        response = self.s3_client.get_object(Bucket=self.bucket, Key=storage_key)
        return response["Body"].read()

    def delete_audio(self, storage_key: str) -> bool:
        self.s3_client.delete_object(Bucket=self.bucket, Key=storage_key)
        audit_logger.info(f"Deleted S3 audio object: key={storage_key}")
        return True


def get_storage_service() -> BaseStorageService:
    if settings.STORAGE_BACKEND.lower() == "s3":
        try:
            return S3StorageService()
        except Exception as e:
            app_logger.warning(f"Failed to initialize S3 storage ({e}), falling back to LocalStorageService")
            return LocalStorageService()
    return LocalStorageService()


storage_service = get_storage_service()
