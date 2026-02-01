from typing import TYPE_CHECKING

import ujson
from aiogram import flags
from stfu_tg import Doc, Section, Template, Title, UserLink, VList

from korone import aredis
from korone.constants import TELEGRAM_ANONYMOUS_ADMIN_BOT_ID
from korone.db.repositories import chat as chat_repo
from korone.filters.cmd import CMDFilter
from korone.modules.utils_.chat_member import update_chat_members
from korone.utils.handlers import KoroneMessageHandler
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType
    from stfu_tg.doc import Element


@flags.help(description=l_("Lists all the chats admins."))
@flags.disableable(name="adminlist")
class AdminListHandler(KoroneMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (CMDFilter(("adminlist", "admins")),)

    async def handle(self) -> None:
        if self.event.chat.type == "private":
            await self.event.reply(_("This command can only be used in groups."))
            return

        chat_model = await chat_repo.get_by_chat_id(self.chat.chat_id)
        if not chat_model:
            await self.event.reply(_("Chat not found."))
            return

        cache_key = f"chat_admins:{chat_model.chat_id}"
        raw = await aredis.get(cache_key)
        if raw is None:
            await update_chat_members(chat_model)
            raw = await aredis.get(cache_key)

        doc = Doc(Title(Template(_("Admins in {chat_name}"), chat_name=self.event.chat.title)))

        admin_items: list[Element] = []
        if raw:
            try:
                admins = ujson.loads(raw.decode() if isinstance(raw, (bytes, bytearray)) else raw)
            except TypeError, ValueError, UnicodeDecodeError:
                admins = {}

            for user_id, admin_data in admins.items():
                user_model = await chat_repo.get_by_chat_id(int(user_id))
                if not user_model:
                    continue

                if user_model.id == TELEGRAM_ANONYMOUS_ADMIN_BOT_ID:
                    continue

                if admin_data.get("is_anonymous"):
                    continue

                admin_items.append(Template(_("{user}"), user=UserLink(user_model.id, user_model.first_name_or_title)))

        if not admin_items:
            doc += _("No visible admins found.")
        else:
            doc += Section(VList(*admin_items), title=_("Admins"))

        await self.event.reply(str(doc), disable_notification=True)
