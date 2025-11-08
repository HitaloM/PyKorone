from aiogram.types import Message, InputMediaPhoto, BufferedInputFile

from sophie_bot.db.models import ChatModel, GreetingsModel, RulesModel
from sophie_bot.db.models.greetings import WelcomeMute
from sophie_bot.modules.greetings.default_welcome import get_default_welcome_message
from sophie_bot.modules.greetings.utils.send_welcome import send_welcome
from sophie_bot.modules.utils_.common_try import common_try
from sophie_bot.modules.welcomesecurity.utils_.emoji_captcha import EmojiCaptcha
from sophie_bot.modules.welcomesecurity.utils_.on_user_passed import ws_on_user_passed
from sophie_bot.services.bot import bot
from sophie_bot.services.redis import aredis
from sophie_bot.utils.i18n import gettext as _


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
        await bot.approve_chat_join_request(chat_id=group.chat_id, user_id=user.chat_id)

    # Unmute user from welcomesecurity (and apply welcome_mute if enabled)
    await ws_on_user_passed(user, group, greetings.welcome_mute or WelcomeMute())

    # Send rules if available
    rules = await RulesModel.get_rules(group.chat_id)
    if rules:
        await send_welcome(captcha_message, rules.saveable, False, None, user)

    # Send welcome message
    if not greetings.welcome_disabled:
        welcome_saveable = greetings.note or get_default_welcome_message(bool(rules))
        await send_welcome(captcha_message, welcome_saveable, False, rules)

    # Clean up
    if msg_to_clean := await aredis.get(f"chat_ws_message:{group.id}:{user.id}"):
        await common_try(bot.delete_message(chat_id=group.chat_id, message_id=int(msg_to_clean)))
        await aredis.delete(f"chat_ws_message:{group.id}:{user.id}")

    if is_join_request:
        if msg_id := await aredis.get(f"join_request_message:{group.id}:{user.id}"):
            await common_try(bot.delete_message(chat_id=group.chat_id, message_id=int(msg_id)))
