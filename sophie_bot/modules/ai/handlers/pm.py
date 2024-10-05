from typing import Any

from aiogram import F, flags
from aiogram.dispatcher.event.handler import CallbackType
from aiogram.handlers import MessageHandler
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from stfu_tg import Bold, Doc, Template, Title, Url

from sophie_bot import CONFIG, bot
from sophie_bot.filters.chat_status import ChatTypeFilter
from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.modules.ai.filters.ai_enabled import AIEnabledFilter
from sophie_bot.modules.ai.filters.throttle import AIThrottleFilter
from sophie_bot.modules.ai.fsm.pm import AI_PM_STOP_TEXT, AiPMFSM
from sophie_bot.modules.ai.utils.ai_chatbot import ai_reply
from sophie_bot.modules.ai.utils.message_history import MessageHistory
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_


@flags.help(description=l_("Start the AI ChatBot mode"))
class AiPmInitialize(MessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return CMDFilter("ai"), ChatTypeFilter("private"), AIEnabledFilter()

    async def handle(self) -> Any:
        doc = Doc(
            Title(_("Beta")),
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

        buttons = ReplyKeyboardMarkup(
            keyboard=[[
                KeyboardButton(text=str(AI_PM_STOP_TEXT)),
            ]],
            resize_keyboard=True,
        )

        state = self.data["state"]
        await state.set_state(AiPMFSM.in_ai)

        await self.event.reply(str(doc), reply_markup=buttons, disable_web_page_preview=True)

        initial_fake_ai_response = _("Hello! How can I help you?")
        await self.event.answer(initial_fake_ai_response)


class AiPmStop(MessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return F.text == AI_PM_STOP_TEXT, ChatTypeFilter("private")  # type: ignore

    async def handle(self) -> Any:
        await self.data["state"].clear()
        await self.event.reply(_("The AI mode has been exited."), reply_markup=ReplyKeyboardRemove())


class AiPmHandle(MessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return AiPMFSM.in_ai, ChatTypeFilter("private"), AIThrottleFilter()

    async def handle(self) -> Any:
        await bot.send_chat_action(self.event.chat.id, "typing")
        messages = await MessageHistory.chatbot(self.event)
        await ai_reply(self.event, messages)
