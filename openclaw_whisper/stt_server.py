"""FastAPI STT server — accepts audio uploads and returns transcribed text."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, HTTPException

from .audio import to_wav_16k
from .config import settings
from .transcriber import Transcriber

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

transcriber: Transcriber | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global transcriber
    settings.whisper.validate()
    transcriber = Transcriber(settings.whisper)
    logger.info("Transcriber ready: model=%s lang=%s", settings.whisper.model_path, settings.whisper.language)
    yield


app = FastAPI(title="OpenClaw Whisper STT", lifespan=lifespan)


@app.post("/transcribe")
async def transcribe(file: UploadFile):
    """Accept an audio file (any format ffmpeg supports) and return text."""
    raw = await file.read()
    if not raw:
        raise HTTPException(400, "Empty file")

    filename = file.filename or ""
    if filename.endswith(".opus"):
        fmt = "opus"
    elif filename.endswith(".ogg"):
        fmt = "ogg"
    elif filename.endswith(".mp3"):
        fmt = "mp3"
    elif filename.endswith(".wav"):
        fmt = "wav"
    else:
        fmt = "wav"

    if fmt != "wav":
        wav_bytes = to_wav_16k(raw, input_format=fmt)
    else:
        wav_bytes = raw

    text = transcriber.transcribe_bytes(wav_bytes)
    return {"text": text}


@app.post("/transcribe_segments")
async def transcribe_segments(file: UploadFile):
    """Accept an audio file and return segments with timestamps."""
    raw = await file.read()
    if not raw:
        raise HTTPException(400, "Empty file")

    filename = file.filename or ""
    if filename.endswith(".opus"):
        fmt = "opus"
    elif filename.endswith(".ogg"):
        fmt = "ogg"
    elif filename.endswith(".mp3"):
        fmt = "mp3"
    elif filename.endswith(".wav"):
        fmt = "wav"
    else:
        fmt = "wav"

    if fmt != "wav":
        wav_bytes = to_wav_16k(raw, input_format=fmt)
    else:
        wav_bytes = raw

    segments = transcriber.transcribe_segments_bytes(wav_bytes)
    return {"segments": segments}


@app.get("/health")
def health():
    return {"status": "ok", "model": settings.whisper.model_path}
