from typing import TYPE_CHECKING, cast

from aiogram import flags
from aiogram.enums import ButtonStyle
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from korone.db.repositories.disabling import DisablingRepository
from korone.filters.admin_rights import UserRestricting
from korone.modules.disabling.callbacks import EnableAllCallback
from korone.modules.utils_.callbacks import CancelActionCallback
from korone.ui import Italic, template
from korone.utils.exception import KoroneError
from korone.utils.handlers import KoroneCallbackQueryHandler, KoroneMessageHandler
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_
from korone.utils.i18n import ngettext as pl_

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType


@flags.help(description=l_("Re-enable all disabled commands in this chat."))
class EnableAllHandler(KoroneMessageHandler):
    @classmethod
    def filters(cls) -> tuple[CallbackType, ...]:
        return (Command("enableall"), UserRestricting(admin=True))

    async def handle(self) -> None:
        if not self.event.from_user:
            raise KoroneError.user_context_unavailable()

        buttons = InlineKeyboardBuilder()
        buttons.button(
            text=_("✅ Enable all"),
            style=ButtonStyle.SUCCESS,
            callback_data=EnableAllCallback(user_id=self.event.from_user.id),
        )
        buttons.button(text=_("❌ Cancel"), style=ButtonStyle.DANGER, callback_data=CancelActionCallback())
        buttons.adjust(2)

        await self.answer(
            template(_("Do you want to enable all commands in the {chat_name}?"), chat_name=Italic(self.chat.title)),
            reply_markup=buttons.as_markup(),
        )


class EnableAllCallbackHandler(KoroneCallbackQueryHandler):
    @classmethod
    def filters(cls) -> tuple[CallbackType, ...]:
        return EnableAllCallback.filter(), UserRestricting(admin=True)

    async def handle(self) -> None:
        data = cast("EnableAllCallback", self.callback_data)
        user_id = self.event.from_user.id

        if user_id != data.user_id:
            await self.event.answer(_("Only the initiator can confirm enabling all commands"))
            return

        model = await DisablingRepository.enable_all(self.chat.chat_id)

        removed_count: int = len(model.cmds) if model else 0

        if removed_count == 0:
            message = _("✅ No commands were enabled in the {chat_name}")
        else:
            message = pl_(
                "✅ {removed_count} command has been enabled in the {chat_name}",
                "✅ {removed_count} commands have been enabled in the {chat_name}",
                removed_count,
            )

        await self.edit_text(template(message, removed_count=Italic(removed_count), chat_name=self.chat.title))
