from random import randint

from aiogram.dispatcher.event.bases import UNHANDLED
from aiohttp import ClientError, ClientSession

from sophie_bot import CONFIG
from sophie_bot.db.models import BetaModeModel, GlobalSettings
from sophie_bot.db.models.beta import CurrentMode, PreferredMode
from sophie_bot.utils.exception import SophieException
from sophie_bot.utils.logger import log

try:
    import ujson as json
except ImportError:
    import json  # type: ignore

from datetime import datetime
from typing import Any, Awaitable, Callable, Optional

from aiogram import BaseMiddleware
from aiogram.types import Chat, TelegramObject


class BetaMiddleware(BaseMiddleware):
    def __init__(self):
        self.session: Optional[ClientSession] = None

    async def get_session(self) -> ClientSession:
        if not self.session:
            self.session = ClientSession()
        return self.session

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        update: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        response = await handler(update, data)
        if response != UNHANDLED:
            return response

        chat: Optional[Chat] = data.get("event_chat")

        json_request = self.get_data(update)
        log.debug("Request data", json_request=json_request)
        if CONFIG.proxy_always_beta or (chat and await self.is_beta(chat.id)):
            log.debug("Sending request to Beta Sophie...")
            await self.send_request(json_request, CONFIG.proxy_beta_instance_url)
        else:
            if self.need_to_drop(update):
                log.debug("Dropping request!!")
                return response

            log.debug("Sending request to Stable Sophie...")
            await self.send_request(json_request, CONFIG.proxy_stable_instance_url)

        return response

    async def is_beta(self, chat_id: int) -> bool:
        model = await BetaModeModel.get_by_chat_id(chat_id)
        # Current mode
        if model and model.mode:
            if model.mode == CurrentMode.beta:
                return True
            elif model.mode == CurrentMode.stable:
                return False

        # If it has a preferred mode
        if model and model.preferred_mode:
            if model.preferred_mode == PreferredMode.beta:
                return True
            elif model.preferred_mode == PreferredMode.stable:
                return False

        # Random
        gs_beta_db = await GlobalSettings.get_by_key("beta_percentage")
        percentage = int(gs_beta_db.value) if gs_beta_db else 0

        if percentage <= 0:
            return False

        new_mode = CurrentMode.beta if randint(0, 100) <= percentage else CurrentMode.stable
        log.debug("Random beta mode generated", chat_id=chat_id, new_mode=new_mode)
        await BetaModeModel.set_mode(chat_id=chat_id, new_mode=new_mode)

        return new_mode == CurrentMode.beta

    @staticmethod
    def need_to_drop(update: TelegramObject) -> bool:
        """Only for Stable. Whatever to drop the update."""

        # Drop all chat_member updates
        if hasattr(update, "chat_member") and update.chat_member:
            return True

        return False

    def get_data(self, update: TelegramObject):
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
