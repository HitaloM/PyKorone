from typing import TYPE_CHECKING, cast

from aiogram.types import Message

from korone.modules.troubleshooters.callbacks import CallbackActionCancel, CancelCallback
from korone.modules.utils_.admin import is_user_admin
from korone.modules.utils_.callbacks import CancelActionCallback
from korone.utils.formatting import Template, UserLink
from korone.utils.handlers import KoroneCallbackQueryHandler
from korone.utils.i18n import gettext as _

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType


class CancelCallbackHandler(KoroneCallbackQueryHandler):
    @classmethod
    def filters(cls) -> tuple[CallbackType, ...]:
        return (CancelActionCallback.filter(),)

    async def handle(self) -> None:
        await self.check_for_message()

        user = self.event.from_user
        message = self.event.message

        if not isinstance(message, Message) or not message.chat:
            return

        if not await is_user_admin(message.chat.id, user.id):
            await self.event.answer(_("You are not allowed to cancel this action!"))
            return

        await self.state.clear()
        await self.edit_text(_("❌ Cancelled."))


class TypedCancelCallbackHandler(KoroneCallbackQueryHandler):
    @classmethod
    def filters(cls) -> tuple[CallbackType, ...]:
        return (CancelCallback.filter(),)

    async def handle(self) -> None:
        data = cast("CancelCallback", self.callback_data)

        user = self.event.from_user

        if user.id != data.user_id:
            await self.event.answer(_("You are not allowed to cancel this action!"))
            return

        await self.state.clear()
        await self.edit_text(_("❌ Cancelled."))


class CallbackActionCancelHandler(KoroneCallbackQueryHandler):
    @classmethod
    def filters(cls) -> tuple[CallbackType, ...]:
        return (CallbackActionCancel.filter(),)

    async def handle(self) -> None:
        user = self.event.from_user
        if not user:
            return

        if not await is_user_admin(self.chat.db_model.chat_id, self.data["user_db"].chat_id):
            await self.event.answer(_("You are not allowed to cancel this action!"))
            return

        await self.state.clear()
        await self.edit_text(
            Template(_("The action was cancelled by {user}."), user=UserLink(user.id, user.first_name)).to_html()
        )
