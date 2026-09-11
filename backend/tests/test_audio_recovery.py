import io
import wave
import pytest
from pathlib import Path
from backend.services.recover_audio import is_valid_wav, recover_file


def test_is_valid_wav_on_real_wav(tmp_path: Path):
    wav_path = tmp_path / "valid.wav"
    with wave.open(str(wav_path), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(16000)
        f.writeframes(b"\x00\x00" * 100)

    assert is_valid_wav(wav_path) is True


def test_is_valid_wav_on_raw_pcm(tmp_path: Path):
    pcm_path = tmp_path / "raw.pcm"
    pcm_path.write_bytes(b"\x00\x00" * 100)
    assert is_valid_wav(pcm_path) is False


def test_recover_file(tmp_path: Path):
    src_pcm = tmp_path / "raw.pcm"
    src_pcm.write_bytes(b"\x01\x00" * 200)

    dst_wav = tmp_path / "recovered.wav"
    ok = recover_file(src_pcm, dst_wav)
    assert ok is True
    assert dst_wav.exists()
    assert is_valid_wav(dst_wav) is True
