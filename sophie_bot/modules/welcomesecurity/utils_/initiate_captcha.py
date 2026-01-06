from aiogram.types import BufferedInputFile, InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from stfu_tg import Bold, Italic, Template

from sophie_bot.db.models import ChatModel
from sophie_bot.modules.welcomesecurity.callbacks import WelcomeSecurityMoveCB, WelcomeSecurityConfirmCB
from sophie_bot.modules.welcomesecurity.utils_.emoji_captcha import EmojiCaptcha
from sophie_bot.services.bot import bot
from sophie_bot.utils.i18n import gettext as _


async def initiate_captcha(
    user: ChatModel,
    group: ChatModel,
    is_join_request: bool = False,
) -> Message:
    """
    Generic function to initiate captcha process.

    Args:
        user: The user to send captcha to
        group: The group chat
        :param is_join_request: Whether this was from a join request
    Returns:
        The message containing the captcha
    """
    # Generate captcha
    captcha = EmojiCaptcha()

    # Create text
    text = Template(
        _("Complete the '{emoji_name}' emoji in order to complete the captcha and participate in the {group_name}."),
        emoji_name=Bold(captcha.data.base_emoji),
        group_name=Italic(group.first_name_or_title),
    )

    # Create buttons
    buttons = InlineKeyboardBuilder()
    buttons.row(
        InlineKeyboardButton(
            text="⬅️",
            callback_data=WelcomeSecurityMoveCB(
                direction="left", chat_iid=str(group.iid), is_join_request=is_join_request
            ).pack(),
        ),
        InlineKeyboardButton(
            text="▶️",
            callback_data=WelcomeSecurityMoveCB(
                direction="right", chat_iid=str(group.iid), is_join_request=is_join_request
            ).pack(),
        ),
    )
    buttons.row(
        InlineKeyboardButton(
            text=f"☑️ {_('Confirm')}",
            callback_data=WelcomeSecurityConfirmCB(chat_iid=str(group.iid), is_join_request=is_join_request).pack(),
        )
    )

    # DM mode: send to user's DM
    return await bot.send_photo(
        chat_id=user.tid,
        photo=BufferedInputFile(captcha.image, "captcha.jpeg"),
        caption=str(text),
        reply_markup=buttons.as_markup(),
    )
