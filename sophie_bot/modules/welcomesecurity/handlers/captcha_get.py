from typing import Any, Optional

from aiogram import Router, flags
from aiogram.types import BufferedInputFile, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from beanie import PydanticObjectId
from stfu_tg import Bold, Italic, Template

from sophie_bot.db.models import ChatModel
from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.filters.user_status import IsOP
from sophie_bot.modules.utils_.base_handler import SophieMessageCallbackQueryHandler
from sophie_bot.modules.welcomesecurity.callbacks import (
    WelcomeSecurityConfirmCB,
    WelcomeSecurityMoveCB,
)
from sophie_bot.modules.welcomesecurity.utils_.emoji_captcha import EmojiCaptcha
from sophie_bot.utils.exception import SophieException
from sophie_bot.utils.i18n import gettext as _


@flags.help(exclude=True)
class CaptchaGetHandler(SophieMessageCallbackQueryHandler):
    @classmethod
    def register(cls, router: Router):
        router.message.register(cls, CMDFilter("captcha"), IsOP(True))
        router.callback_query.register(cls, WelcomeSecurityMoveCB.filter())

    async def handle(self) -> Any:
        state_data = await self.state.get_data()

        # Try to get chat_iid from state, then from callback_data, then from data
        chat_iid = state_data.get("ws_chat_iid") or self.data.get("ws_chat_iid")
        if not chat_iid and hasattr(self, "callback_data") and self.callback_data:
            if hasattr(self.callback_data, "chat_iid") and self.callback_data.chat_iid:
                chat_iid = self.callback_data.chat_iid

        if not chat_iid:
            await self.answer(
                _(
                    (
                        "The chat initiated the Welcome Security procedure were not found! "
                        "Try clicking on the authentication button in the group again."
                    )
                )
            )
            await self.state.clear()
            return

        chat_db = await ChatModel.get_by_iid(PydanticObjectId(chat_iid))
        if not chat_db:
            await self.answer(_("Chat not found in database"))
            await self.state.clear()
            return

        shuffle: bool = self.data.get("ws_shuffle", False)

        # Restore from state or generate new
        captcha = EmojiCaptcha(data=state_data.get("captcha") if not shuffle else None)

        cb_data: Optional[WelcomeSecurityMoveCB] = self.data.get("callback_data")
        is_join_request: bool = cb_data.is_join_request if cb_data else False

        if not cb_data or not isinstance(cb_data, WelcomeSecurityMoveCB):
            pass
        elif cb_data.direction == "left":
            captcha.data.move_to_left()
        elif cb_data.direction == "right":
            captcha.data.move_to_right()
        else:
            raise SophieException("Invalid direction")

        text = Template(
            _(
                "Complete the '{emoji_name}' emoji in order to complete the captcha and participate in the {group_name}."
            ),
            emoji_name=Bold(captcha.data.base_emoji),
            group_name=Italic(chat_db.first_name_or_title),
        )

        if shuffle:
            text += ""
            text += Bold(_("❌ Incorrect solution. Please, try again."))

        buttons = InlineKeyboardBuilder()
        buttons.row(
            InlineKeyboardButton(
                text="⬅️", callback_data=WelcomeSecurityMoveCB(direction="left", is_join_request=is_join_request).pack()
            ),
            InlineKeyboardButton(
                text="▶️", callback_data=WelcomeSecurityMoveCB(direction="right", is_join_request=is_join_request).pack()
            ),
        )
        buttons.row(
            InlineKeyboardButton(
                text=f"☑️ {_('Confirm')}", callback_data=WelcomeSecurityConfirmCB(is_join_request=is_join_request).pack()
            )
        )

        await self.answer_media(
            BufferedInputFile(captcha.image, "captcha.jpeg"),
            caption=str(text),
            reply_markup=buttons.as_markup(),
        )

        await self.state.update_data({"captcha": captcha.data.model_dump(), "ws_chat_iid": str(chat_db.id)})
