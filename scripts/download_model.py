"""Download and validate the configured faster-whisper model."""

from __future__ import annotations

import os

from dotenv import load_dotenv


def main() -> int:
    load_dotenv()
    from faster_whisper import WhisperModel

    model_size = os.getenv("ASR_MODEL", "small")
    device = os.getenv("ASR_DEVICE", "cpu")
    compute_type = os.getenv("ASR_COMPUTE_TYPE", "int8" if device == "cpu" else "float16")
    print(f"Downloading/loading faster-whisper model: {model_size} ({device}, {compute_type})")
    WhisperModel(model_size, device=device, compute_type=compute_type)
    print("Model is ready.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
