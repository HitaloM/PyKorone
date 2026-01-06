from aiogram.dispatcher.event.handler import CallbackType
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from stfu_tg import Italic, Template

from sophie_bot.db.models import DisablingModel
from sophie_bot.filters.admin_rights import UserRestricting
from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.modules.disabling.callbacks import EnableAllCallback
from sophie_bot.modules.utils_.base_handler import (
    SophieCallbackQueryHandler,
    SophieMessageHandler,
)
from sophie_bot.utils.exception import SophieException
from sophie_bot.utils.i18n import gettext as _


class EnableAllHandler(SophieMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return CMDFilter("enableall"), UserRestricting(admin=True)

    async def handle(self):
        connection = self.connection

        if not self.event.from_user:
            raise SophieException("Not a user clicked a button")

        buttons = InlineKeyboardBuilder()
        buttons.add(
            InlineKeyboardButton(
                text=_("✅ Enable all"), callback_data=EnableAllCallback(user_id=self.event.from_user.id).pack()
            ),
        )
        buttons.add(
            InlineKeyboardButton(text=_("🚫 Cancel"), callback_data="cancel"),
        )

        return await self.event.reply(
            text=str(
                Template(
                    _("Do you want to enable all commands in the {chat_name}?"), chat_name=Italic(connection.title)
                )
            ),
            reply_markup=buttons.as_markup(),
        )


class DisableAllCbHandler(SophieCallbackQueryHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return EnableAllCallback.filter(), UserRestricting(admin=True)

    async def handle(self):
        connection = self.connection

        data: EnableAllCallback = self.data["callback_data"]
        user_id = self.event.from_user.id

        if user_id != data.user_id:
            return await self.event.answer(_("Only the initiator can confirm disabling all commands"))

        model = await DisablingModel.enable_all(connection.tid)

        removed_count: int = len(model.cmds) if model else 0

        return await self.event.message.edit_text(  # type: ignore
            str(
                Template(
                    _("✅ All the commands ({removed_count}) have been enabled in the {chat_name}"),
                    removed_count=Italic(removed_count),
                    chat_name=connection.title,
                )
            )
        )
