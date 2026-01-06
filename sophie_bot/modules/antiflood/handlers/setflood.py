from __future__ import annotations

from typing import Literal

from aiogram import flags
from aiogram.dispatcher.event.handler import CallbackType
from aiogram.types import Message
from ass_tg.types import IntArg, OptionalArg
from ass_tg.types.base_abc import ArgFabric
from stfu_tg import Template

from sophie_bot.db.models.antiflood import AntifloodModel
from sophie_bot.filters.admin_rights import UserRestricting
from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.modules.utils_.status_handler import StatusHandlerABC
from sophie_bot.utils.i18n import lazy_gettext as l_, gettext as _


@flags.help(description=l_("Set the antiflood message threshold"))
@flags.disableable(name="setflood")
class SetFloodHandler(StatusHandlerABC[int | Literal[False]]):
    header_text = l_("Antiflood Message Threshold")
    change_command = "setflood"
    change_args = "off / 5 / 10"
    status_texts = {}  # Will be handled by status_text method override

    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return CMDFilter("setflood"), UserRestricting(admin=True)

    @classmethod
    async def handler_args(cls, message: Message | None, data: dict) -> dict[str, ArgFabric]:
        return {
            "new_status": OptionalArg(IntArg(l_("Number of messages allowed in 30 seconds"))),
        }

    async def get_status(self) -> int:
        """Get the current flood message threshold."""
        antiflood_model = await AntifloodModel.get_by_chat_iid(self.connection.db_model.iid)
        return antiflood_model.message_count

    async def set_status(self, new_status: Literal[False] | int):
        """Set a new flood message threshold."""
        chat_iid = self.connection.db_model.iid

        if new_status is False:
            model = await AntifloodModel.get_by_chat_iid(chat_iid)
            await model.delete()
            return

        await AntifloodModel.set_antiflood_count(chat_iid, new_status)

    def status_text(self, status_data: Literal[False] | int) -> str:
        """Override to provide custom status text formatting."""
        if status_data is False:
            return _("Disabled")
        return Template(_("{status_data} messages in 30 seconds"), status_data=status_data)
