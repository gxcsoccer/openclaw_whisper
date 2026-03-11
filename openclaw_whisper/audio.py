"""Audio format conversion via ffmpeg."""

import logging
import subprocess
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)


def to_wav_16k(input_bytes: bytes, input_format: str = "opus") -> bytes:
    """Convert audio bytes (opus/ogg/mp3/…) to 16 kHz mono WAV via ffmpeg.

    Returns the WAV file content as bytes.
    """
    with tempfile.NamedTemporaryFile(suffix=f".{input_format}", delete=False) as src:
        src.write(input_bytes)
        src_path = src.name

    dst_path = src_path.rsplit(".", 1)[0] + ".wav"

    try:
        cmd = [
            "ffmpeg", "-y",
            "-i", src_path,
            "-ar", "16000",
            "-ac", "1",
            "-sample_fmt", "s16",
            dst_path,
        ]
        logger.info("ffmpeg converting %s → %s", input_format, dst_path)

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg failed: {result.stderr[:500]}")

        return Path(dst_path).read_bytes()
    finally:
        Path(src_path).unlink(missing_ok=True)
        Path(dst_path).unlink(missing_ok=True)
