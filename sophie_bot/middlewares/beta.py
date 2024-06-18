from aiohttp import ClientError, ClientSession

from sophie_bot import CONFIG
from sophie_bot.utils.logger import log

try:
    import ujson as json
except ImportError:
    import json

from datetime import datetime
from typing import Any, Awaitable, Callable, Optional

from aiogram import BaseMiddleware
from aiogram.types import Update


class BetaMiddleware(BaseMiddleware):
    def __init__(self):
        self.session: Optional[ClientSession] = None

    async def get_session(self) -> ClientSession:
        if not self.session:
            self.session = ClientSession()
        return self.session

    async def __call__(
            self, handler: Callable[[Update, dict[str, Any]], Awaitable[Any]], update: Update, data: dict[str, Any]
    ) -> Any:
        result = await handler(update, data)

        log.debug("Sending request to Stable Sophie...")
        await self.send_request(self.get_data(update))

        return result

    def get_data(self, update: Update):
        raw_json = update.model_dump_json(by_alias=True, exclude_none=True, indent=1)
        raw_data = json.loads(raw_json)

        data = self.change_data_type(raw_data)

        return json.dumps(data)

    def change_data_type(self, data: dict) -> dict:
        # Recursively convert all date fields to unix timestamps
        for key, value in data.items():
            if isinstance(value, dict):
                data[key] = self.change_data_type(value)
            elif isinstance(value, str) and "date" in key and "T" in value:
                data[key] = datetime.fromisoformat(value).timestamp()

        return data

    async def send_request(self, json_request: str):
        try:
            session = await self.get_session()
            await session.post(CONFIG.stable_instance_url, data=json_request)
        except ClientError as e:
            raise Exception(
                "Failed to send request to the second backend.", "Please contact support chat."
            ) from e
