"""High-level handler: Feishu audio message → transcribed text.

This is the main integration point for OpenClaw bot.
"""

import logging

from .audio import to_wav_16k
from .config import settings
from .feishu import FeishuClient
from .transcriber import Transcriber

logger = logging.getLogger(__name__)


class SpeechHandler:
    """Process Feishu voice messages into text using local whisper.cpp."""

    def __init__(self):
        self.feishu = FeishuClient(settings.feishu)
        self.transcriber = Transcriber(settings.whisper)

    async def handle_voice_message(self, message_id: str, file_key: str) -> str:
        """Full pipeline: download → convert → transcribe.

        Args:
            message_id: Feishu message ID containing the audio.
            file_key: File key of the audio attachment.

        Returns:
            Transcribed text string.
        """
        # 1. Download audio from Feishu (opus format)
        logger.info("Processing voice message: msg=%s file=%s", message_id, file_key)
        audio_bytes = await self.feishu.download_audio(message_id, file_key)

        # 2. Convert opus → 16kHz mono WAV
        wav_bytes = to_wav_16k(audio_bytes, input_format="opus")

        # 3. Transcribe with whisper.cpp
        text = self.transcriber.transcribe_bytes(wav_bytes)

        logger.info("Voice message transcribed: %s → %s", file_key, text[:80])
        return text
