"""
Recovery script for audio files logged BEFORE the log_session_for_finetuning
fix in mcp_server.py.

Those files are raw 16-bit PCM mono 16kHz samples that were saved directly
to disk with a ".wav" extension but NO RIFF/WAVE header. This script wraps
each one in a proper WAV container so they become playable and usable for
Whisper fine-tuning.

Run this once against your existing dataset/audio directory before retrying
training. It writes fixed copies to a new folder rather than overwriting,
so you can verify before deleting the originals.

Usage:
    python recover_audio.py --src dataset/audio --dst dataset/audio_fixed
"""

import argparse
import wave
from pathlib import Path


def is_valid_wav(path: Path) -> bool:
    """Check if a file already has a real RIFF/WAVE header."""
    try:
        with open(path, "rb") as f:
            header = f.read(12)
        return header[:4] == b"RIFF" and header[8:12] == b"WAVE"
    except Exception:
        return False


def recover_file(src_path: Path, dst_path: Path, framerate: int = 16000,
                  channels: int = 1, sampwidth: int = 2) -> bool:
    """Wrap raw PCM bytes from src_path in a valid WAV header, saved to dst_path."""
    with open(src_path, "rb") as f:
        raw = f.read()

    if len(raw) == 0:
        return False

    with wave.open(str(dst_path), "wb") as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(sampwidth)
        wav_file.setframerate(framerate)
        wav_file.writeframes(raw)

    return True


def main():
    parser = argparse.ArgumentParser(description="Recover headerless PCM files into valid WAVs.")
    parser.add_argument("--src", default="dataset/audio", help="Folder with the broken .wav files")
    parser.add_argument("--dst", default="dataset/audio_fixed", help="Folder to write recovered .wav files")
    parser.add_argument("--framerate", type=int, default=16000)
    parser.add_argument("--channels", type=int, default=1)
    parser.add_argument("--sampwidth", type=int, default=2, help="Bytes per sample (2 = 16-bit PCM)")
    args = parser.parse_args()

    src_dir = Path(args.src)
    dst_dir = Path(args.dst)
    dst_dir.mkdir(parents=True, exist_ok=True)

    wav_files = sorted(src_dir.glob("*.wav"))
    print(f"Found {len(wav_files)} files in {src_dir}")

    recovered, already_valid, empty_or_failed = 0, 0, 0

    for src_path in wav_files:
        if is_valid_wav(src_path):
            print(f"  [already valid] {src_path.name} -- copying as-is")
            dst_path = dst_dir / src_path.name
            dst_path.write_bytes(src_path.read_bytes())
            already_valid += 1
            continue

        dst_path = dst_dir / src_path.name
        ok = recover_file(
            src_path, dst_path,
            framerate=args.framerate,
            channels=args.channels,
            sampwidth=args.sampwidth,
        )
        if ok:
            print(f"  [recovered]     {src_path.name}")
            recovered += 1
        else:
            print(f"  [EMPTY/FAILED]  {src_path.name} -- 0 bytes, nothing to recover")
            empty_or_failed += 1

    print("\n--- Summary ---")
    print(f"Already valid WAVs : {already_valid}")
    print(f"Recovered          : {recovered}")
    print(f"Empty/unrecoverable: {empty_or_failed}")
    print(f"\nFixed files written to: {dst_dir.resolve()}")
    print("Update your JSONL's audio_filepath entries (or your path-correction cell) to point here.")


if __name__ == "__main__":
    main()