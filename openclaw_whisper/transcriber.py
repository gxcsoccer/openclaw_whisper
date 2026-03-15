"""whisper.cpp wrapper — calls the binary and returns transcribed text."""

import logging
import subprocess
import tempfile
from pathlib import Path

from .config import WhisperConfig

logger = logging.getLogger(__name__)


class Transcriber:
    def __init__(self, config: WhisperConfig):
        config.validate()
        self.cfg = config

    def transcribe(self, wav_path: str | Path) -> str:
        """Transcribe a 16 kHz mono WAV file and return plain text."""
        wav_path = Path(wav_path)
        if not wav_path.is_file():
            raise FileNotFoundError(f"WAV file not found: {wav_path}")

        cmd = [
            self.cfg.bin_path,
            "-m", self.cfg.model_path,
            "-f", str(wav_path),
            "-l", self.cfg.language,
            "--no-timestamps",
            "--no-prints",      # suppress progress/debug output
            "-t", str(self.cfg.threads),
        ]
        logger.info("Running whisper.cpp: %s", " ".join(cmd))

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=1800,  # 30 min: ~1h video on M4 Pro Metal  # large-v3 on long audio may take a while
        )

        if result.returncode != 0:
            logger.error("whisper.cpp stderr: %s", result.stderr)
            raise RuntimeError(f"whisper.cpp failed (rc={result.returncode}): {result.stderr[:500]}")

        # whisper-cli outputs transcription on stdout, one line per segment
        # Filter out any remaining log lines (start with "whisper_" or "ggml_" etc.)
        lines = []
        for line in result.stdout.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            # Skip known log prefixes that sneak through
            if any(stripped.startswith(p) for p in (
                "whisper_", "ggml_", "metal_", "system_info",
                "main:", "output_",
            )):
                continue
            lines.append(stripped)

        text = "\n".join(lines)
        logger.info("Transcription (%d chars): %s", len(text), text[:80])
        return text

    def transcribe_segments(self, wav_path: str | Path) -> list[dict]:
        """Transcribe a 16 kHz mono WAV file and return segments with timestamps.

        Returns a list of dicts: [{"start": 0.0, "end": 5.2, "text": "..."}, ...]
        """
        wav_path = Path(wav_path)
        if not wav_path.is_file():
            raise FileNotFoundError(f"WAV file not found: {wav_path}")

        cmd = [
            self.cfg.bin_path,
            "-m", self.cfg.model_path,
            "-f", str(wav_path),
            "-l", self.cfg.language,
            "--no-prints",      # suppress progress/debug output
            "-t", str(self.cfg.threads),
        ]
        logger.info("Running whisper.cpp (segments): %s", " ".join(cmd))

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=1800,  # 30 min: ~1h video on M4 Pro Metal
        )

        if result.returncode != 0:
            logger.error("whisper.cpp stderr: %s", result.stderr)
            raise RuntimeError(f"whisper.cpp failed (rc={result.returncode}): {result.stderr[:500]}")

        import re
        segments = []
        # whisper.cpp timestamp format: [HH:MM:SS.mmm --> HH:MM:SS.mmm]  text
        ts_pattern = re.compile(
            r"\[(\d{2}):(\d{2}):(\d{2}\.\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}\.\d{3})\]\s*(.*)"
        )
        for line in result.stdout.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            if any(stripped.startswith(p) for p in (
                "whisper_", "ggml_", "metal_", "system_info", "main:", "output_",
            )):
                continue
            m = ts_pattern.match(stripped)
            if m:
                start = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
                end = int(m.group(4)) * 3600 + int(m.group(5)) * 60 + float(m.group(6))
                text = m.group(7).strip()
                if text:
                    segments.append({"start": round(start, 3), "end": round(end, 3), "text": text})

        logger.info("Transcription segments: %d segments", len(segments))
        return segments

    def transcribe_bytes(self, audio_wav: bytes) -> str:
        """Convenience: write bytes to a temp file, transcribe, clean up."""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio_wav)
            tmp_path = tmp.name
        try:
            return self.transcribe(tmp_path)
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def transcribe_segments_bytes(self, audio_wav: bytes) -> list[dict]:
        """Convenience: write bytes to a temp file, transcribe segments, clean up."""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio_wav)
            tmp_path = tmp.name
        try:
            return self.transcribe_segments(tmp_path)
        finally:
            Path(tmp_path).unlink(missing_ok=True)
