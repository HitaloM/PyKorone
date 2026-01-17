from typing import Any

from aiogram import F
from aiogram.dispatcher.event.handler import CallbackType

from sophie_bot.modules.utils_.admin import is_user_admin
from sophie_bot.modules.troubleshooters.callbacks import CancelCallback
from sophie_bot.modules.utils_.base_handler import SophieCallbackQueryHandler
from sophie_bot.utils.i18n import gettext as _


class CancelCallbackHandler(SophieCallbackQueryHandler):
    """
    Mostly used in the wizards and other dialogs.
    Cancels the current state and deletes the message.
    The user has to be an admin to use this
    """

    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (F.data == "cancel",)

    async def handle(self) -> Any:
        await self.check_for_message()

        user = self.event.from_user

        if not is_user_admin(self.event.message.chat.id, user.id):  # type: ignore[union-attr]
            return await self.event.answer(_("You are not allowed to cancel this action!"))

        await self.state.clear()
        await self.event.message.edit_text(_("❌ Cancelled."))  # type: ignore[union-attr]


class TypedCancelCallbackHandler(SophieCallbackQueryHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (CancelCallback.filter(),)

    async def handle(self) -> Any:
        data: CancelCallback = self.callback_data

        user = self.event.from_user

        if user.id != data.user_id:
            return await self.event.answer(_("You are not allowed to cancel this action!"))

        await self.state.clear()
        await self.event.message.edit_text(_("❌ Cancelled."))  # type: ignore[union-attr]
