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
            timeout=300,  # large-v3 on long audio may take a while
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

    def transcribe_bytes(self, audio_wav: bytes) -> str:
        """Convenience: write bytes to a temp file, transcribe, clean up."""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio_wav)
            tmp_path = tmp.name
        try:
            return self.transcribe(tmp_path)
        finally:
            Path(tmp_path).unlink(missing_ok=True)
