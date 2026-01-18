from typing import Any

from aiogram import F
from aiogram.dispatcher.event.handler import CallbackType

from sophie_bot.config import CONFIG
from sophie_bot.db.models import (
    ChatModel,
    GreetingsModel,
    UserInGroupModel,
    WSUserModel,
)
from sophie_bot.modules.utils_.admin import is_user_admin
from sophie_bot.utils.handlers import (
    SophieCallbackQueryHandler,
    SophieMessageHandler,
)
from sophie_bot.modules.welcomesecurity.handlers.captcha_get import CaptchaGetHandler
from sophie_bot.utils.exception import SophieException
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.logger import log


class LegacyStableWSButtonRedirectHandler(SophieCallbackQueryHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (F.data.startswith("ws_"),)

    async def handle(self) -> Any:
        chat_id = self.event.message.chat.id
        return self.event.answer(url=f"https://t.me/{CONFIG.username}?start=btnwelcomesecuritystart_{chat_id}")


class LegacyWSButtonHandler(SophieMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (F.text.regexp(r"/start btnwelcomesecuritystart_(.*)"),)

    async def handle(self) -> Any:
        _prefix, chat_id = self.event.text.split("_", 2)
        chat_id = int(chat_id)

        if not (group_db := await ChatModel.get_by_tid(chat_id)):
            raise SophieException("Cannot find group")

        user_db: ChatModel = self.data["user_db"]

        if not await UserInGroupModel.get_user_in_group(user_db.iid, group_db.iid):
            return await self.event.reply(
                _("It seems like you are not belong to the chat anymore. Are you sure you joined the group?")
            )

        if await is_user_admin(chat_id, user_db.iid):
            # TODO: Make it unmute the muted user instead
            return await self.event.reply(
                _("You already an admin in the chat, therefore you don't need to pass the authentication!")
            )

        if not await WSUserModel.is_user(user_db.iid, group_db.iid):
            return await self.event.reply(
                _("It seems like you do not have to pass the welcome security authentication")
            )

        # TODO: Check if not banned / fedbanned

        ws_db_item = await GreetingsModel.get_by_chat_id(chat_id)

        if not ws_db_item.welcome_security or not ws_db_item.welcome_security.enabled:
            # We still allow users to complete it, because it could've been disabled afterwards
            log.debug("LegacyWSButtonHandler: WS is disabled but we still allow users to complete")

        # Initialize captcha
        self.data["ws_chat_iid"] = group_db.iid
        return await CaptchaGetHandler(self.event, **self.data).handle()
