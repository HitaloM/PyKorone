from aiogram import flags
from aiogram.dispatcher.event.handler import CallbackType
from aiogram.types import InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from stfu_tg import Italic, Template

from korone.db.models.disabling import DisablingModel
from korone.filters.admin_rights import UserRestricting
from korone.filters.cmd import CMDFilter
from korone.modules.disabling.callbacks import EnableAllCallback
from korone.modules.utils_.callbacks import CancelActionCallback
from korone.utils.exception import KoroneException
from korone.utils.handlers import KoroneCallbackQueryHandler, KoroneMessageHandler
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_


@flags.help(description=l_("Enable all commands in the chat"))
class EnableAllHandler(KoroneMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return CMDFilter("enableall"), UserRestricting(admin=True)

    async def handle(self):
        if not self.event.from_user:
            raise KoroneException("Not a user clicked a button")

        buttons = InlineKeyboardBuilder()
        buttons.add(
            InlineKeyboardButton(
                text=_("✅ Enable all"), callback_data=EnableAllCallback(user_id=self.event.from_user.id).pack()
            )
        )
        buttons.add(InlineKeyboardButton(text=_("🚫 Cancel"), callback_data=CancelActionCallback().pack()))

        return await self.event.reply(
            text=str(
                Template(_("Do you want to enable all commands in the {chat_name}?"), chat_name=Italic(self.chat.title))
            ),
            reply_markup=buttons.as_markup(),
        )


class DisableAllCbHandler(KoroneCallbackQueryHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return EnableAllCallback.filter(), UserRestricting(admin=True)

    async def handle(self):
        data: EnableAllCallback = self.data["callback_data"]
        user_id = self.event.from_user.id

        if user_id != data.user_id:
            return await self.event.answer(_("Only the initiator can confirm disabling all commands"))

        model = await DisablingModel.enable_all(self.chat.tid)

        removed_count: int = len(model.cmds) if model else 0

        message = self.event.message
        if isinstance(message, Message):
            return await message.edit_text(
                str(
                    Template(
                        _("✅ All the commands ({removed_count}) have been enabled in the {chat_name}"),
                        removed_count=Italic(removed_count),
                        chat_name=self.chat.title,
                    )
                )
            )
