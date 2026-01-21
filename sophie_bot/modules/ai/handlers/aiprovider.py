from __future__ import annotations

from typing import Any

from aiogram import F, flags
from aiogram.dispatcher.event.handler import CallbackType
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from stfu_tg import Doc, KeyValue, Section

from sophie_bot.db.models.ai.ai_provider import AIProviderModel
from sophie_bot.filters.admin_rights import UserRestricting
from sophie_bot.filters.chat_status import ChatTypeFilter
from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.modules.ai.callbacks import AIProviderCallback
from sophie_bot.modules.ai.fsm.pm import AI_PM_PROVIDER
from sophie_bot.modules.ai.utils.ai_models import (
    AI_PROVIDER_TO_NAME,
    AVAILABLE_PROVIDER_NAMES,
    AIProviders,
)
from sophie_bot.modules.utils_.admin import is_user_admin
from sophie_bot.utils.handlers import (
    SophieCallbackQueryHandler,
    SophieMessageHandler,
)
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_

PROVIDERS_KEY_FACTS: dict[AIProviders, Any] = {
    AIProviders.auto: l_("🔃 Automatically choose the best provider"),
    AIProviders.google: l_("⚡️ The fastest"),
    AIProviders.mistral: l_("🔒 The most private"),
    AIProviders.openai: l_("🧠 The smartest"),
    AIProviders.anthropic: l_("👨‍🏫 The most precise"),
    AIProviders.zai: l_("💻 Best for coding"),
}


def build_keyboard(selected: str) -> InlineKeyboardMarkup:
    """Build keyboard with AI provider options, marking the selected one."""
    rows = []
    for name in AVAILABLE_PROVIDER_NAMES:
        title = AI_PROVIDER_TO_NAME[name]
        mark = "✅ " if name == selected else ""
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"{mark}{title} - {PROVIDERS_KEY_FACTS[AIProviders[name]]}",
                    callback_data=AIProviderCallback(provider=name).pack(),
                )
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=rows)


@flags.help(description=l_("Select the AI Provider for this chat"))
class AIProviderSetting(SophieMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return CMDFilter(("aiprovider",)), UserRestricting(admin=True)

    async def handle(self):
        if not self.connection.db_model:
            return
        chat = self.connection.db_model
        current = await AIProviderModel.get_provider_name(chat.iid)
        current = current or AIProviders.auto.name

        kb = build_keyboard(current)

        doc = Doc(
            Section(
                KeyValue(_("Current provider"), AI_PROVIDER_TO_NAME[current]),
                title=l_("AI Provider"),
            )
        )
        await self.event.reply(str(doc), reply_markup=kb)


class AIProviderSelectCallback(SophieCallbackQueryHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (AIProviderCallback.filter(),)

    async def handle(self):
        await self.check_for_message()
        data: AIProviderCallback = self.callback_data

        if not isinstance(self.event.message, Message):
            return await self.event.answer(_("Invalid message type"))

        message = self.event.message
        chat_id = message.chat.id
        user = self.event.from_user

        # ensure only admins can change
        if not is_user_admin(chat_id, user.id):
            return await self.event.answer(_("You are not allowed to change this setting"))

        # validate provider
        provider_name = data.provider
        if provider_name not in AVAILABLE_PROVIDER_NAMES:
            return await self.event.answer(_("Unknown provider"))

        await AIProviderModel.set_provider(self.connection.db_model, provider_name)

        doc = Doc(
            Section(
                KeyValue(_("Chat"), self.connection.title),
                KeyValue(_("New provider"), AI_PROVIDER_TO_NAME[provider_name]),
                title=l_("AI Provider was updated"),
            )
        )
        await message.edit_text(str(doc))
        await self.event.answer(_("Provider updated"))
        return None


@flags.help(description=l_("Select the AI Provider for this chat"))
class AIProviderSettingAlt(AIProviderSetting):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return F.text == AI_PM_PROVIDER, ChatTypeFilter("private")
