from typing import Any

from aiogram.dispatcher.event.handler import CallbackType
from aiogram.filters import or_f
from aiogram.types import Message
from beanie import PydanticObjectId

from sophie_bot.db.models import ChatModel, GreetingsModel, RulesModel
from sophie_bot.modules.utils_.base_handler import SophieCallbackQueryHandler
from sophie_bot.modules.utils_.common_try import common_try
from sophie_bot.modules.welcomesecurity.callbacks import (
    WelcomeSecurityConfirmCB,
    WelcomeSecurityRulesAgreeCB,
)
from sophie_bot.modules.welcomesecurity.handlers.captcha_get import CaptchaGetHandler
from sophie_bot.modules.welcomesecurity.utils_.captcha_done import captcha_done
from sophie_bot.modules.welcomesecurity.utils_.captcha_rules import captcha_send_rules
from sophie_bot.modules.welcomesecurity.utils_.emoji_captcha import EmojiCaptcha
from sophie_bot.services.bot import bot
from sophie_bot.services.redis import aredis
from sophie_bot.utils.exception import SophieException


class CaptchaConfirmHandler(SophieCallbackQueryHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (or_f(WelcomeSecurityConfirmCB().filter(), WelcomeSecurityRulesAgreeCB().filter()),)

    async def captcha_correct(self, group: ChatModel, state_data: dict[str, Any]):
        if not isinstance(self.event.message, Message):
            raise SophieException("Invalid message type. Try initializing the captcha again.")

        user = self.data["user_db"]

        if not isinstance(self.data["callback_data"], WelcomeSecurityRulesAgreeCB) and (
            rules := await RulesModel.get_rules(chat_id=group.chat_id)
        ):
            return await captcha_send_rules(self.event.message, rules)

        # Cleanup
        if msg_to_clean := await aredis.get(f"chat_ws_message:{group.id}:{user.id}"):
            chat_db = await ChatModel.get_by_iid(PydanticObjectId(state_data["ws_chat_iid"]))
            if chat_db:
                await common_try(bot.delete_message(chat_id=chat_db.chat_id, message_id=msg_to_clean))
        await self.state.clear()

        locale = self.current_locale
        greetings_db = await GreetingsModel.get_by_chat_id(group.chat_id)

        return await captcha_done(self.event, user, group, greetings_db, locale)

    async def handle(self) -> Any:
        data = await self.state.get_data()

        chat_db = await ChatModel.get_by_iid(PydanticObjectId(data["ws_chat_iid"]))
        if not chat_db:
            raise ValueError("No chat found in database")

        if "captcha" not in data:
            raise ValueError("No captcha data found in FSM context")

        captcha = EmojiCaptcha(data=data["captcha"])

        if captcha.data.is_correct:
            return await self.captcha_correct(chat_db, data)
        else:
            self.data["ws_shuffle"] = True
            return await CaptchaGetHandler(self.event, **self.data)
