from __future__ import annotations

import asyncio
import json
import time
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from korone.utils.aiohttp_session import HTTPClient

from .helpers import request_id

if TYPE_CHECKING:
    from .settings import VulcanAPISettings


def _parse_token_expiration(raw_value: object) -> float:
    if isinstance(raw_value, (int, float)):
        return float(raw_value)

    if isinstance(raw_value, str):
        normalized = raw_value.replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(normalized)
        except ValueError:
            return time.time() + 300

        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)

        return parsed.timestamp()

    return time.time() + 300


class VulcanTokenManager:
    def __init__(self, settings: VulcanAPISettings) -> None:
        self._settings = settings
        self._access_token: str | None = None
        self._expires_at_unix: float = 0.0
        self._lock = asyncio.Lock()

    def invalidate(self) -> None:
        self._expires_at_unix = 0.0

    async def get_valid_token(self) -> str:
        current_time = time.time()
        if self._access_token and current_time < (self._expires_at_unix - 30):
            return self._access_token

        async with self._lock:
            current_time = time.time()
            if self._access_token and current_time < (self._expires_at_unix - 30):
                return self._access_token

            await self._refresh_token()
            if self._access_token:
                return self._access_token

            msg = "Could not obtain Vulcan access token"
            raise RuntimeError(msg)

    async def _refresh_token(self) -> None:
        headers = {
            "X-Vulcan-Application-ID": self._settings.application_id,
            "Accept": "application/json",
            "User-Agent": self._settings.token_user_agent,
            "X-Vulcan-Request-ID": request_id(self._settings.request_id_prefix),
            "Content-Type": "application/json; charset=utf-8",
        }
        payload = {
            "device_id": self._settings.device_id,
            "order_id": "",
            "product_id": "",
            "purchase_token": "",
            "subscription_id": "",
        }
        session = await HTTPClient.get_session()
        async with session.post(self._settings.auth_url, json=payload, headers=headers) as response:
            response.raise_for_status()
            raw_body = await response.text()

        try:
            body_obj: object = json.loads(raw_body)
        except json.JSONDecodeError as exc:
            msg = "Vulcan token response must be valid JSON"
            raise TypeError(msg) from exc

        if not isinstance(body_obj, dict):
            msg = "Vulcan token response must be a JSON object"
            raise TypeError(msg)

        access_token = body_obj.get("AccessToken")
        if not isinstance(access_token, str) or not access_token:
            msg = "Vulcan token response missing AccessToken"
            raise RuntimeError(msg)

        self._access_token = access_token
        self._expires_at_unix = _parse_token_expiration(body_obj.get("AccessTokenExpiration"))
