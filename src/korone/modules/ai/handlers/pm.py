from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram import F, flags
from aiogram.filters import StateFilter
from aiogram.types import CallbackQuery, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from stfu_tg import Bold, Doc, Template, Url

from korone.config import CONFIG
from korone.filters.chat_status import PrivateChatFilter
from korone.filters.cmd import CMDFilter
from korone.modules.ai.callbacks import AIChatCallback
from korone.modules.ai.fsm.pm import AI_PM_RESET, AI_PM_STOP_TEXT, AiPMFSM
from korone.modules.ai.utils.ai_chatbot_reply import ai_chatbot_reply
from korone.utils.handlers import KoroneMessageCallbackQueryHandler, KoroneMessageHandler
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from aiogram import Router
    from aiogram.dispatcher.event.handler import CallbackType
    from aiogram.types import Message


def ai_pm_buttons() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=str(AI_PM_STOP_TEXT)), KeyboardButton(text=str(AI_PM_RESET))]],
        resize_keyboard=True,
    )


@flags.help(exclude=True)
class AiPmInitialize(KoroneMessageCallbackQueryHandler):
    @classmethod
    def register(cls, router: Router) -> None:
        router.message.register(cls, CMDFilter("ai"), PrivateChatFilter())
        router.callback_query.register(cls, PrivateChatFilter(), AIChatCallback.filter())

    async def handle(self) -> None:
        doc = Doc(
            Bold(_("🤖 Entered AI mode. You can now chat directly with Korone AI.")),
            Template(
                _("By using AI, you agree to the bot and provider {privacy_policy}."),
                privacy_policy=Url(_("privacy policy"), CONFIG.privacy_link),
            ),
            _("Use the keyboard button below to exit or reset context."),
        )

        await self.state.set_state(AiPMFSM.in_ai)
        if isinstance(self.event, CallbackQuery):
            await self.event.answer()
        await self.message.answer(str(doc), disable_web_page_preview=True)
        await self.message.answer(_("Hello! How can I help you?"), reply_markup=ai_pm_buttons())


@flags.help(exclude=True)
class AiPmStop(KoroneMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (F.text == AI_PM_STOP_TEXT, PrivateChatFilter())

    async def handle(self) -> None:
        await self.state.clear()
        await self.event.reply(_("The AI mode has been exited."), reply_markup=ReplyKeyboardRemove())


@flags.help(description=l_("Reply directly in PM while AI mode is active"), exclude=True)
class AiPmHandle(KoroneMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (StateFilter(AiPMFSM.in_ai), PrivateChatFilter())

    async def handle(self) -> Message | None:
        # Dedicated handlers process stop/reset buttons before this handler.
        if self.event.text in {str(AI_PM_STOP_TEXT), str(AI_PM_RESET)}:
            return None
        if self.event.text and self.event.text.startswith(tuple(CONFIG.commands_prefix)):
            return None

        return await ai_chatbot_reply(self.event, self.chat, reply_markup=ai_pm_buttons())
