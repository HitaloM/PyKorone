from typing import Any

from aiogram import F, Router, flags
from aiogram.dispatcher.event.handler import CallbackType
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from stfu_tg import Bold, Doc, Template, Url

from sophie_bot.config import CONFIG
from sophie_bot.filters.chat_status import ChatTypeFilter
from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.modules.ai.callbacks import AIChatCallback
from sophie_bot.modules.ai.filters.throttle import AIThrottleFilter
from sophie_bot.modules.ai.fsm.pm import AI_PM_PROVIDER, AI_PM_RESET, AI_PM_STOP_TEXT, AiPMFSM
from sophie_bot.modules.ai.utils.ai_chatbot_reply import ai_chatbot_reply
from sophie_bot.modules.utils_.base_handler import (
    SophieMessageCallbackQueryHandler,
    SophieMessageHandler,
)
from sophie_bot.services.bot import bot
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_


@flags.help(description=l_("Start the AI ChatBot mode"))
class AiPmInitialize(SophieMessageCallbackQueryHandler):
    @classmethod
    def register(cls, router: Router):
        router.message.register(cls, CMDFilter("ai"), ChatTypeFilter("private"))
        router.callback_query.register(cls, AIChatCallback.filter(), ChatTypeFilter("private"))

    async def handle(self) -> Any:
        doc = Doc(
            Bold(
                Template(
                    _("{ai_emoji} Entered to the AI Mode, in this mode you can directly interact with the AI."),
                    ai_emoji=CONFIG.ai_emoji,
                )
            ),
            Template(
                _("By using the AI, you agree to the {privacy_policy} of the bot and third party AI services used."),
                privacy_policy=Url(_("privacy policy"), CONFIG.privacy_link),
            ),
            _("Click on the button below to exit."),
        )

        state = self.data["state"]
        await state.set_state(AiPMFSM.in_ai)

        await self.answer(str(doc), disable_web_page_preview=True)

        initial_fake_ai_response = _("Hello! How can I help you?")
        buttons = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text=str(AI_PM_STOP_TEXT)), KeyboardButton(text=str(AI_PM_RESET))],
                [KeyboardButton(text=str(AI_PM_PROVIDER))],
            ],
            resize_keyboard=True,
        )
        await self.message.answer(initial_fake_ai_response, reply_markup=buttons)


class AiPmStop(SophieMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return F.text == AI_PM_STOP_TEXT, ChatTypeFilter("private")

    async def handle(self) -> Any:
        await self.data["state"].clear()
        await self.event.reply(_("The AI mode has been exited."), reply_markup=ReplyKeyboardRemove())


@flags.ai_cache(cache_handler_result=True)
class AiPmHandle(SophieMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return AiPMFSM.in_ai, ChatTypeFilter("private"), AIThrottleFilter()

    async def handle(self) -> Any:
        await bot.send_chat_action(self.event.chat.id, "typing")
        buttons = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text=str(AI_PM_STOP_TEXT)), KeyboardButton(text=str(AI_PM_RESET))],
                [KeyboardButton(text=str(AI_PM_PROVIDER))],
            ],
            resize_keyboard=True,
        )

        self.data["ai_msg_cache"] = True
        return await ai_chatbot_reply(self.event, self.connection, reply_markup=buttons)
