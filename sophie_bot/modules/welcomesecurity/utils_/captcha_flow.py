from typing import Optional

from aiogram.types import BufferedInputFile, InlineKeyboardButton, InputMediaPhoto, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from stfu_tg import Bold, Italic, Template

from sophie_bot.db.models import ChatModel, GreetingsModel, RulesModel
from sophie_bot.modules.greetings.default_welcome import get_default_welcome_message
from sophie_bot.modules.greetings.utils.send_welcome import send_welcome
from sophie_bot.modules.utils_.common_try import common_try
from sophie_bot.modules.welcomesecurity.utils_.emoji_captcha import EmojiCaptcha
from sophie_bot.modules.welcomesecurity.utils_.on_user_passed import ws_on_user_passed
from sophie_bot.services.bot import bot
from sophie_bot.services.redis import aredis
from sophie_bot.utils.i18n import gettext as _


async def initiate_captcha(
    user: ChatModel,
    group: ChatModel,
    greetings: GreetingsModel,
    send_to_chat: bool = False,
    chat_message: Optional[Message] = None,
) -> Message:
    """
    Generic function to initiate captcha process.

    Args:
        user: The user to send captcha to
        group: The group chat
        greetings: Greetings model
        send_to_chat: If True, send captcha in group chat (legacy), else in DM
        chat_message: The message in chat (for editing in legacy mode)

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
    from sophie_bot.modules.welcomesecurity.callbacks import WelcomeSecurityConfirmCB, WelcomeSecurityMoveCB

    buttons = InlineKeyboardBuilder()
    buttons.row(
        InlineKeyboardButton(
            text="⬅️", callback_data=WelcomeSecurityMoveCB(direction="left", chat_iid=str(group.id)).pack()
        ),
        InlineKeyboardButton(
            text="▶️", callback_data=WelcomeSecurityMoveCB(direction="right", chat_iid=str(group.id)).pack()
        ),
    )
    buttons.row(
        InlineKeyboardButton(
            text=f"☑️ {_('Confirm')}", callback_data=WelcomeSecurityConfirmCB(chat_iid=str(group.id)).pack()
        )
    )

    if send_to_chat and chat_message:
        # Legacy mode: edit the chat message
        result = await bot.edit_message_media(
            media=InputMediaPhoto(media=BufferedInputFile(captcha.image, "captcha.jpeg"), caption=str(text)),
            chat_id=chat_message.chat.id,
            message_id=chat_message.message_id,
            reply_markup=buttons.as_markup(),
        )
        return result if isinstance(result, Message) else chat_message
    else:
        # DM mode: send to user's DM
        try:
            return await bot.send_photo(
                chat_id=user.chat_id,
                photo=BufferedInputFile(captcha.image, "captcha.jpeg"),
                caption=str(text),
                reply_markup=buttons.as_markup(),
            )
        except Exception:
            # If can't send to DM, fallback to chat
            if chat_message:
                result = await bot.edit_message_media(
                    media=InputMediaPhoto(media=BufferedInputFile(captcha.image, "captcha.jpeg"), caption=str(text)),
                    chat_id=chat_message.chat.id,
                    message_id=chat_message.message_id,
                    reply_markup=buttons.as_markup(),
                )
                return result if isinstance(result, Message) else chat_message
            raise


async def complete_captcha(
    user: ChatModel,
    group: ChatModel,
    greetings: GreetingsModel,
    captcha_message: Message,
    is_join_request: bool = False,
):
    """
    Generic function to complete captcha process.

    Args:
        user: The user who completed captcha
        group: The group chat
        greetings: Greetings model
        captcha_message: The message containing the captcha
        is_join_request: Whether this was from a join request
    """
    # Mark captcha as correct
    captcha = EmojiCaptcha()
    captcha.show_emoji("✅")

    # Update the captcha message
    await bot.edit_message_media(
        media=InputMediaPhoto(
            media=BufferedInputFile(captcha.image, "captcha.jpeg"),
            caption=_("You're all set, and can now participate in the conversation"),
        ),
        chat_id=captcha_message.chat.id,
        message_id=captcha_message.message_id,
    )

    # Approve join request if applicable
    if is_join_request:
        try:
            await bot.approve_chat_join_request(chat_id=group.chat_id, user_id=user.chat_id)
        except Exception:
            pass

    # Unmute user
    if greetings.welcome_mute and greetings.welcome_mute.enabled and greetings.welcome_mute.time:
        await ws_on_user_passed(user, group, greetings.welcome_mute)

    # Send rules if available
    rules = await RulesModel.get_rules(group.chat_id)
    if rules:
        if is_join_request:
            await bot.send_message(chat_id=user.chat_id, text=str(rules.saveable.text or ""))
        else:
            await send_welcome(captcha_message, rules.saveable, False, None)

    # Send welcome message
    if not greetings.welcome_disabled:
        welcome_saveable = greetings.note or get_default_welcome_message(bool(rules))
        if is_join_request:
            # For join requests, send welcome in DM
            await bot.send_message(chat_id=user.chat_id, text=str(welcome_saveable.text or ""))
        else:
            # For legacy, send in chat
            await send_welcome(captcha_message, welcome_saveable, False, rules)

    # Clean up
    if msg_to_clean := await aredis.get(f"chat_ws_message:{group.id}:{user.id}"):
        await common_try(bot.delete_message(chat_id=group.chat_id, message_id=int(msg_to_clean)))
        await aredis.delete(f"chat_ws_message:{group.id}:{user.id}")

    if is_join_request:
        if msg_id := await aredis.get(f"join_request_message:{group.id}:{user.id}"):
            await common_try(bot.delete_message(chat_id=group.chat_id, message_id=int(msg_id)))
            await aredis.delete(f"join_request_message:{group.id}:{user.id}")
