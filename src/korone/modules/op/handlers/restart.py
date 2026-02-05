from __future__ import annotations

from typing import TYPE_CHECKING, cast

from aiogram import flags
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from anyio import Lock
from stfu_tg import Doc

from korone.config import CONFIG
from korone.filters.cmd import CMDFilter
from korone.filters.user_status import IsOP
from korone.logger import get_logger
from korone.modules.op.callbacks import OpRestartCallback
from korone.modules.op.utils import restart_bot, save_restart_marker
from korone.utils.handlers import KoroneCallbackQueryHandler, KoroneMessageHandler
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType
    from aiogram.types import Message

logger = get_logger(__name__)
RESTART_LOCK = Lock()


@flags.help(description=l_("Restart the bot without updating."))
class OpRestartHandler(KoroneMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (CMDFilter(("restart", "reboot")), IsOP(is_op=True))

    async def handle(self) -> None:
        if not self.event.from_user:
            return

        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(
                text=_("Confirm restart"), callback_data=OpRestartCallback(initiator_id=self.event.from_user.id).pack()
            )
        )

        await self.event.reply(
            str(Doc(_("Are you sure you want to restart the bot?"))), reply_markup=builder.as_markup()
        )


@flags.help(exclude=True)
class OpRestartCallbackHandler(KoroneCallbackQueryHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (OpRestartCallback.filter(),)

    async def handle(self) -> None:
        if not self.event.from_user:
            return

        if self.event.from_user.id not in CONFIG.operators:
            await self.event.answer(_("Not allowed."), show_alert=True)
            return

        callback_data = cast("OpRestartCallback", self.callback_data)
        if callback_data.initiator_id != self.event.from_user.id:
            await self.event.answer(_("Only the requester can confirm this restart."), show_alert=True)
            return

        await self.event.answer(_("Restarting..."))

        async with RESTART_LOCK:
            await self.check_for_message()
            await self.edit_text(_("Restarting now..."))
            await logger.ainfo("op_restart: restart requested", user_id=self.event.from_user.id)
            message = cast("Message", self.event.message)
            await save_restart_marker(chat_id=message.chat.id, message_id=message.message_id, action="restart")
            await restart_bot()
