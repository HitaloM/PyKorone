# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from __future__ import annotations

import httpx

API_BASE_URL = "https://api.mcsrvstat.us/3"


class MinecraftServerStatus:
    def __init__(self, data: dict) -> None:
        self.online = data.get("online", False)
        self.version = data.get("version", "N/A") if self.online else "Unknown"
        self.motd = data.get("motd", {}).get("clean", "") if self.online else ""
        self.players_online = data.get("players", {}).get("online", 0) if self.online else 0
        self.players_max = data.get("players", {}).get("max", 0) if self.online else 0

    @classmethod
    async def from_address(cls, address: str) -> MinecraftServerStatus:
        url = f"{API_BASE_URL}/{address}"
        try:
            async with httpx.AsyncClient(http2=True) as client:
                response = await client.get(url)
                response.raise_for_status()
            data = response.json()
        except (httpx.RequestError, httpx.HTTPStatusError, ValueError) as exc:
            msg = f"An error occurred while requesting {url}: {exc}"
            raise RuntimeError(msg) from exc

        return cls(data)

    @property
    def player_count(self) -> str:
        return f"{self.players_online}/{self.players_max}"
