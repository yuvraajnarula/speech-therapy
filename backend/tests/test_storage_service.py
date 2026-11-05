"""
Tests for backend/app/services/storage_service.py — HIPAA-safe audio storage.

Covers: local storage anonymization (SHA-256 content hashing), upload/get/delete,
S3 client fallback behavior, and storage backend selection.
"""
import hashlib
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from backend.app.services.storage_service import (
    BaseStorageService,
    LocalStorageService,
    S3StorageService,
    get_storage_service,
    storage_service,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_s3_client():
    client = MagicMock()
    client.get_object.return_value = {"Body": MagicMock(read=lambda: b"retrieved-pcm")}
    return client


# ---------------------------------------------------------------------------
# BaseStorageService
# ---------------------------------------------------------------------------

def test_base_storage_service_is_abstract():
    """BaseStorageService should not be directly instantiable for upload."""
    svc = BaseStorageService()
    with pytest.raises(NotImplementedError):
        svc.upload_audio_bytes(b"pcm data")


# ---------------------------------------------------------------------------
# LocalStorageService
# ---------------------------------------------------------------------------

def test_local_upload_creates_anonymized_filename(tmp_path):
    """Uploaded audio is saved under a SHA-256 content hash, never raw PII."""
    svc = LocalStorageService(base_dir=str(tmp_path))
    audio = b"fake-pcm-audio-bytes-12345"
    key = svc.upload_audio_bytes(audio, filename_prefix="session")

    expected_hash = hashlib.sha256(audio).hexdigest()[:16]
    expected_name = f"session_{expected_hash}.wav"
    assert key.endswith(expected_name)

    saved_path = Path(key)
    assert saved_path.exists()
    assert saved_path.read_bytes() == audio


def test_local_upload_is_deterministic(tmp_path):
    """Same audio bytes always produce the same storage key."""
    svc = LocalStorageService(base_dir=str(tmp_path))
    audio = b"deterministic-audio-payload"
    k1 = svc.upload_audio_bytes(audio, filename_prefix="attempt")
    k2 = svc.upload_audio_bytes(audio, filename_prefix="attempt")
    assert k1 == k2


def test_local_get_and_delete(tmp_path):
    """Round-trip: upload -> get -> delete."""
    svc = LocalStorageService(base_dir=str(tmp_path))
    audio = b"round-trip-pcm-data"
    key = svc.upload_audio_bytes(audio, filename_prefix="rt")

    assert svc.get_audio_bytes(key) == audio
    assert svc.delete_audio(key) is True
    assert not Path(key).exists()


def test_local_get_missing_file_raises(tmp_path):
    """Getting a non-existent storage key raises FileNotFoundError."""
    svc = LocalStorageService(base_dir=str(tmp_path))
    with pytest.raises(FileNotFoundError):
        svc.get_audio_bytes(str(tmp_path / "does_not_exist.wav"))


def test_local_delete_missing_file_returns_false(tmp_path):
    """Deleting a non-existent file returns False (idempotent)."""
    svc = LocalStorageService(base_dir=str(tmp_path))
    assert svc.delete_audio(str(tmp_path / "does_not_exist.wav")) is False


# ---------------------------------------------------------------------------
# S3StorageService (mocked)
# ---------------------------------------------------------------------------

def test_s3_upload_uses_server_side_encryption(tmp_path, monkeypatch):
    """When ENCRYPT_AUDIO_AT_REST is set, S3 upload includes AES256."""
    monkeypatch.setenv("STORAGE_BACKEND", "s3")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "test-key")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "test-secret")
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("S3_BUCKET_NAME", "test-bucket")
    monkeypatch.setenv("ENCRYPT_AUDIO_AT_REST", "true")

    from backend.app.core import config as cfg
    monkeypatch.setattr(cfg.settings, "S3_BUCKET_NAME", "test-bucket")
    monkeypatch.setattr(cfg.settings, "ENCRYPT_AUDIO_AT_REST", True)

    mock_client = MagicMock()
    with patch("boto3.client", return_value=mock_client):
        svc = S3StorageService()
        svc.upload_audio_bytes(b"s3-pcm-data", filename_prefix="s3")

    call_kwargs = mock_client.put_object.call_args.kwargs
    assert call_kwargs["Bucket"] == "test-bucket"
    assert call_kwargs["ContentType"] == "audio/wav"
    assert call_kwargs.get("ServerSideEncryption") == "AES256"


def test_s3_get_and_delete(mock_s3_client):
    """S3 get/delete delegate to the boto3 client."""
    with patch("boto3.client", return_value=mock_s3_client):
        svc = S3StorageService()
        svc.s3_client = mock_s3_client
        svc.bucket = "test-bucket"

        mock_s3_client.get_object.return_value = {"Body": MagicMock(read=lambda: b"retrieved-pcm")}
        data = svc.get_audio_bytes("audio/key.wav")
        assert data == b"retrieved-pcm"

        svc.delete_audio("audio/key.wav")
        mock_s3_client.delete_object.assert_called_once_with(Bucket="test-bucket", Key="audio/key.wav")


# ---------------------------------------------------------------------------
# get_storage_service factory
# ---------------------------------------------------------------------------

def test_get_storage_service_defaults_to_local(monkeypatch, tmp_path):
    """With no S3 env vars, factory returns LocalStorageService."""
    monkeypatch.setenv("STORAGE_BACKEND", "local")
    monkeypatch.setenv("LOCAL_STORAGE_DIR", str(tmp_path))
    svc = get_storage_service()
    assert isinstance(svc, LocalStorageService)


def test_get_storage_service_s3_falls_back_to_local(monkeypatch, tmp_path):
    """If S3 init fails, factory falls back to LocalStorageService."""
    monkeypatch.setenv("STORAGE_BACKEND", "s3")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "x")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "y")
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("S3_BUCKET_NAME", "bucket")
    monkeypatch.setenv("LOCAL_STORAGE_DIR", str(tmp_path))

    with patch("backend.app.services.storage_service.S3StorageService", side_effect=Exception("boom")):
        svc = get_storage_service()
        assert isinstance(svc, LocalStorageService)


# ---------------------------------------------------------------------------
# module singleton
# ---------------------------------------------------------------------------

def test_storage_service_singleton_is_local():
    """The imported `storage_service` singleton is a BaseStorageService instance."""
    assert isinstance(storage_service, BaseStorageService)
