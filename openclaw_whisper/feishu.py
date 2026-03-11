"""Feishu (Lark) API helpers — token management and file download."""

import logging
import time

import httpx

from .config import FeishuConfig

logger = logging.getLogger(__name__)

FEISHU_BASE = "https://open.feishu.cn/open-apis"


class FeishuClient:
    def __init__(self, config: FeishuConfig):
        self.cfg = config
        self._token: str = ""
        self._token_expires: float = 0

    async def _ensure_token(self, client: httpx.AsyncClient):
        """Get or refresh tenant_access_token."""
        if self._token and time.time() < self._token_expires:
            return

        resp = await client.post(
            f"{FEISHU_BASE}/auth/v3/tenant_access_token/internal",
            json={
                "app_id": self.cfg.app_id,
                "app_secret": self.cfg.app_secret,
            },
        )
        resp.raise_for_status()
        data = resp.json()

        if data.get("code") != 0:
            raise RuntimeError(f"Feishu token error: {data}")

        self._token = data["tenant_access_token"]
        # expire 5 minutes early to be safe
        self._token_expires = time.time() + data.get("expire", 7200) - 300
        logger.info("Feishu token refreshed, expires in %ds", data.get("expire", 0))

    async def download_audio(self, message_id: str, file_key: str) -> bytes:
        """Download an audio file from a Feishu message.

        Uses the message resource download API:
        GET /im/v1/messages/:message_id/resources/:file_key?type=file
        """
        async with httpx.AsyncClient(timeout=30) as client:
            await self._ensure_token(client)

            url = f"{FEISHU_BASE}/im/v1/messages/{message_id}/resources/{file_key}"
            resp = await client.get(
                url,
                params={"type": "file"},
                headers={"Authorization": f"Bearer {self._token}"},
            )
            resp.raise_for_status()

            logger.info(
                "Downloaded feishu audio: message=%s file=%s size=%d",
                message_id, file_key, len(resp.content),
            )
            return resp.content
