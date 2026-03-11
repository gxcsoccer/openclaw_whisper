"""Entry point: python -m openclaw_whisper"""

import uvicorn

from .config import settings

if __name__ == "__main__":
    uvicorn.run(
        "openclaw_whisper.stt_server:app",
        host=settings.stt_host,
        port=settings.stt_port,
        reload=False,
    )
