from datetime import timedelta
from typing import Any, Optional

from aiogram.types import CallbackQuery, Message
from aiogram.utils.i18n import I18n
from ass_tg.entities import ArgEntities
from ass_tg.exceptions import ARGS_EXCEPTIONS
from ass_tg.i18n import gettext_ctx
from ass_tg.types import ActionTimeArg
from babel.dates import format_timedelta
from pydantic import BaseModel
from stfu_tg import KeyValue, Template, Title, UserLink
from stfu_tg.doc import Doc, Element

from sophie_bot.modules.filters.types.modern_action_abc import (
    ActionSetupMessage,
    ActionSetupTryAgainException,
    ModernActionABC,
    ModernActionSetting,
)
from sophie_bot.modules.restrictions.utils import ban_user, is_user_admin
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_
from sophie_bot.utils.logger import log


class BanActionDataModel(BaseModel):
    ban_duration: Optional[timedelta]


async def setup_confirm(event: Message | CallbackQuery, data: dict[str, Any]) -> BanActionDataModel:
    if isinstance(event, CallbackQuery):
        raise ValueError("This handlers setup_confirm can only be used with messages")

    raw_text = event.text or ""

    # Permanent ban
    if raw_text == "0":
        return BanActionDataModel(ban_duration=None)

    try:
        i18n = I18n(path="/")
        gettext_ctx.set(i18n)

        with i18n.context():
            arg: timedelta = (await ActionTimeArg().parse(raw_text, 0, ArgEntities([])))[1]
    except ARGS_EXCEPTIONS:
        # TODO: Properly validate
        await event.reply(_("Invalid ban duration, please try again."))
        raise ActionSetupTryAgainException()

    return BanActionDataModel(ban_duration=arg)


async def setup_message(_event: Message | CallbackQuery, _data: dict[str, Any]) -> ActionSetupMessage:
    return ActionSetupMessage(
        text=_(
            "Please write the ban duration, for example 2h for 2 hours, 7d for 7 days or 2w for 2 weeks. Or 0 for a permanent ban."
        ),
    )


class BanModernAction(ModernActionABC[BanActionDataModel]):
    name = "ban_user"
    icon = "🚷"
    title = l_("Ban")
    data_object = BanActionDataModel
    default_data = BanActionDataModel(ban_duration=None)
    as_flood = True

    @staticmethod
    def description(data: BanActionDataModel) -> Element | str:
        if data.ban_duration:
            # TODO: not en_US
            return Template(_("Bans user for {time}"), time=format_timedelta(data.ban_duration, locale="en_US"))

        return _("Bans user indefinitely")

    def settings(self, data: BanActionDataModel) -> dict[str, ModernActionSetting]:
        return {
            "change_ban_duration": ModernActionSetting(
                title=l_("Change ban duration"),
                icon="⏰",
                setup_message=setup_message,
                setup_confirm=setup_confirm,
            ),
        }

    async def handle(self, message: Message, data: dict, filter_data: BanActionDataModel) -> Optional[Element]:
        if not message.from_user:
            return

        chat_id = message.chat.id
        user_id = message.from_user.id
        locale: str = data["i18n"].current_locale

        if await is_user_admin(chat_id, user_id):
            log.debug("BanModernAction: user is admin, skipping...")
            return

        doc = Doc(
            Title(_("Filter action")),
            Template(
                _("User {user} was automatically banned based on a filter action"),
                user=UserLink(message.from_user.id, message.from_user.first_name),
            ),
        )

        if filter_data.ban_duration:
            doc += KeyValue(_("For"), format_timedelta(filter_data.ban_duration, locale=locale))

        if not await ban_user(chat_id, message.from_user.id, until_date=filter_data.ban_duration):
            return

        return doc
