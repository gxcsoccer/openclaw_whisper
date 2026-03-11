import os
from pathlib import Path
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


@dataclass
class WhisperConfig:
    bin_path: str = ""
    model_path: str = ""
    language: str = "zh"
    threads: int = 8

    def __post_init__(self):
        self.bin_path = self.bin_path or os.getenv("WHISPER_BIN", "")
        self.model_path = self.model_path or os.getenv("WHISPER_MODEL", "")
        self.language = self.language or os.getenv("WHISPER_LANGUAGE", "zh")
        self.threads = self.threads or int(os.getenv("WHISPER_THREADS", "8"))

    def validate(self):
        if not Path(self.bin_path).is_file():
            raise FileNotFoundError(f"whisper.cpp binary not found: {self.bin_path}")
        if not Path(self.model_path).is_file():
            raise FileNotFoundError(f"whisper model not found: {self.model_path}")


@dataclass
class FeishuConfig:
    app_id: str = ""
    app_secret: str = ""

    def __post_init__(self):
        self.app_id = self.app_id or os.getenv("FEISHU_APP_ID", "")
        self.app_secret = self.app_secret or os.getenv("FEISHU_APP_SECRET", "")


@dataclass
class Settings:
    whisper: WhisperConfig = field(default_factory=WhisperConfig)
    feishu: FeishuConfig = field(default_factory=FeishuConfig)
    stt_host: str = ""
    stt_port: int = 8765

    def __post_init__(self):
        self.stt_host = self.stt_host or os.getenv("STT_HOST", "0.0.0.0")
        self.stt_port = self.stt_port or int(os.getenv("STT_PORT", "8765"))


settings = Settings()
