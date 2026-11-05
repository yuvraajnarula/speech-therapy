import json
import sys
from pathlib import Path
from backend.services.repoint_jsonl import main


def test_repoint_jsonl_replaces_audio_dir(tmp_path, monkeypatch):
    src = tmp_path / "manifest.jsonl"
    out = tmp_path / "repointed.jsonl"

    records = [
        {"audio_filepath": "dataset/audio/hello.wav", "text": "hello"},
        {"audio_filepath": "dataset/audio/world.wav", "text": "world"},
        {"audio_filepath": "other/path/foo.wav", "text": "foo"},
        {"no_audio_field": "bar"},
    ]
    src.write_text("\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8")

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "repoint_jsonl.py",
            "--src",
            str(src),
            "--out",
            str(out),
            "--old-dir",
            "dataset/audio",
            "--new-dir",
            "dataset/audio_fixed",
        ],
    )

    main()

    result = [json.loads(l) for l in out.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert result[0]["audio_filepath"] == "dataset/audio_fixed/hello.wav"
    assert result[1]["audio_filepath"] == "dataset/audio_fixed/world.wav"
    assert result[2]["audio_filepath"] == "other/path/foo.wav"  # unchanged
    assert result[3] == {"no_audio_field": "bar"}  # missing field preserved


def test_repoint_jsonl_default_fields(tmp_path, monkeypatch):
    src = tmp_path / "manifest.jsonl"
    out = tmp_path / "repointed.jsonl"

    src.write_text(
        json.dumps({"audio_filepath": "dataset/audio/test.wav", "text": "test"})
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        sys,
        "argv",
        ["repoint_jsonl.py", "--src", str(src), "--out", str(out)],
    )

    main()

    result = json.loads(out.read_text(encoding="utf-8").strip())
    assert result["audio_filepath"] == "dataset/audio_fixed/test.wav"


def test_repoint_jsonl_empty_file(tmp_path, monkeypatch):
    src = tmp_path / "empty.jsonl"
    out = tmp_path / "out.jsonl"
    src.write_text("", encoding="utf-8")

    monkeypatch.setattr(
        sys,
        "argv",
        ["repoint_jsonl.py", "--src", str(src), "--out", str(out)],
    )

    main()

    assert out.read_text(encoding="utf-8") == ""
