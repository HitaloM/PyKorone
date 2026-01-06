from datetime import timedelta
from typing import Literal, Optional

from aiogram import flags
from aiogram.dispatcher.event.handler import CallbackType
from aiogram.types import Message
from ass_tg.types import ActionTimeArg, BooleanArg, OptionalArg, OrArg, TextArg
from ass_tg.types.base_abc import ArgFabric
from babel.dates import format_timedelta
from stfu_tg import Italic, Template
from stfu_tg.doc import Element

from sophie_bot.db.models import GreetingsModel
from sophie_bot.filters.admin_rights import UserRestricting
from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.modules.legacy_modules.utils.message import convert_time
from sophie_bot.modules.utils_.status_handler import StatusHandlerABC
from sophie_bot.modules.welcomesecurity.utils_.db_time_convert import (
    convert_timedelta_or_str,
)
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_


@flags.help(
    description=l_("Shows / changes the state of Welcome Restrict (Media restricting)."),
    args={"NewStatus": TextArg(l_("?New status or restrict time"))},
)
class EnableWelcomeMute(StatusHandlerABC[timedelta | str | Literal[False]]):
    header_text = l_("Welcome Mute (Automatic new users media restricting)")
    change_command = "welcomerestrict"
    change_args = "off / 12h / 2d / 1w"

    @classmethod
    async def handler_args(cls, message: Message | None, data: dict) -> dict[str, ArgFabric]:
        return {"new_status": OptionalArg(OrArg(ActionTimeArg(l_("? Action time")), BooleanArg("?New status")))}

    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return CMDFilter("welcomerestrict"), UserRestricting(admin=True)

    def status_text(self, status_data: timedelta | str | bool) -> Element | str:
        locale = self.current_locale

        # From db
        if isinstance(status_data, str):
            delta = convert_time(status_data)
        elif isinstance(status_data, bool) and not status_data:
            return _("Disabled")
        elif isinstance(status_data, timedelta):
            delta = status_data
        else:
            raise ValueError("Invalid status data type")

        return Template(_("Enabled, set to {time}"), time=Italic(format_timedelta(delta, locale=locale)))

    async def get_status(self) -> timedelta | Literal[False]:
        chat_id = self.connection.tid
        db_model = await GreetingsModel.get_by_chat_id(chat_id)

        if not db_model or not db_model.welcome_mute or not db_model.welcome_mute.enabled:
            return False

        if db_model.welcome_mute.time is None:
            return False
        return convert_timedelta_or_str(db_model.welcome_mute.time)

    async def set_status(self, new_status: str | timedelta | Literal[False]):
        chat_id = self.connection.tid

        time: Optional[timedelta] = None

        if isinstance(new_status, bool) and not new_status:
            is_enabled = False
        else:
            is_enabled = True
            time = convert_timedelta_or_str(new_status)

        db_model = await GreetingsModel.get_by_chat_id(chat_id)

        time_str = str(time) if time else None
        await db_model.set_status_welcomemute(is_enabled, time_str)
