from __future__ import annotations

from aiogram import flags
from aiogram.dispatcher.event.handler import CallbackType

from sophie_bot.db.models.antiflood import AntifloodModel
from sophie_bot.filters.admin_rights import UserRestricting
from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.filters.feature_flag import FeatureFlagFilter
from sophie_bot.modules.utils_.status_handler import StatusBoolHandlerABC
from sophie_bot.utils.i18n import lazy_gettext as l_


@flags.help(alias_to_modules=["restrictions"], description=l_("Controls antiflood protection"))
@flags.disableable(name="antiflood")
class AntifloodSetting(StatusBoolHandlerABC):
    """Handler for toggling antiflood protection on/off."""

    header_text = l_("📈 Antiflood")
    change_command = "antiflood"

    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (
            CMDFilter(("antiflood", "flood")),
            UserRestricting(admin=True),
            FeatureFlagFilter("antiflood"),
        )

    async def get_status(self) -> bool:
        if not self.connection.db_model:
            return False
        settings = await AntifloodModel.find_one(AntifloodModel.chat.id == self.connection.db_model.iid)
        return bool(settings and settings.enabled)

    async def set_status(self, new_status: bool) -> None:
        if not self.connection.db_model:
            return
        chat_iid = self.connection.db_model.iid
        settings = await AntifloodModel.find_one(AntifloodModel.chat.id == chat_iid)

        if settings:
            settings.enabled = new_status
            await settings.save()
        elif new_status:
            # Create new settings only if enabling
            new_settings = AntifloodModel(chat=self.connection.db_model, enabled=True)
            await new_settings.save()
