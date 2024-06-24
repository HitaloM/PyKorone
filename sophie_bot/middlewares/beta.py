from aiogram.dispatcher.event.bases import UNHANDLED
from aiohttp import ClientError, ClientSession

from sophie_bot import CONFIG
from sophie_bot.db.cache.beta import cache_get_chat_beta
from sophie_bot.utils.exception import SophieException
from sophie_bot.utils.logger import log

try:
    import ujson as json
except ImportError:
    import json

from datetime import datetime
from typing import Any, Awaitable, Callable, Optional

from aiogram import BaseMiddleware
from aiogram.types import Chat, Update


class BetaMiddleware(BaseMiddleware):
    def __init__(self):
        self.session: Optional[ClientSession] = None

    async def get_session(self) -> ClientSession:
        if not self.session:
            self.session = ClientSession()
        return self.session

    async def __call__(
        self,
        handler: Callable[[Update, dict[str, Any]], Awaitable[Any]],
        update: Update,
        data: dict[str, Any],
    ) -> Any:
        response = await handler(update, data)
        if response != UNHANDLED:
            return response

        chat: Optional[Chat] = data.get("event_chat")

        json_request = self.get_data(update)
        log.debug("Request data", json_request=json_request)
        if CONFIG.proxy_always_beta or (chat and await cache_get_chat_beta(chat.id)):
            log.debug("Sending request to Beta Sophie...")
            await self.send_request(json_request, CONFIG.proxy_beta_instance_url)
        else:
            log.debug("Sending request to Stable Sophie...")
            await self.send_request(json_request, CONFIG.proxy_stable_instance_url)

        return response

    def get_data(self, update: Update):
        raw_json = update.model_dump_json(by_alias=True, exclude_none=True, exclude_defaults=True, indent=1)
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

    async def send_request(self, json_request: str, instance_url: str):
        try:
            session = await self.get_session()
            await session.post(instance_url, data=json_request)
        except ClientError as e:
            raise SophieException(
                "Failed to send request to the second backend.",
                "Please contact support chat.",
            ) from e
