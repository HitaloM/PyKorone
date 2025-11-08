from aiogram.types import CallbackQuery, InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from babel.dates import format_timedelta
from stfu_tg import Doc, Template

from sophie_bot.db.models import ChatModel, GreetingsModel, RulesModel
from sophie_bot.modules.greetings.default_welcome import get_default_welcome_message
from sophie_bot.modules.greetings.utils.send_welcome import send_welcome
from sophie_bot.modules.welcomesecurity.utils_.db_time_convert import (
    convert_timedelta_or_str,
)
from sophie_bot.modules.welcomesecurity.utils_.emoji_captcha import EmojiCaptcha
from sophie_bot.modules.welcomesecurity.utils_.on_user_passed import ws_on_user_passed
from sophie_bot.modules.welcomesecurity.utils_.send_captcha import send_captcha_message
from sophie_bot.utils.exception import SophieException
from sophie_bot.utils.i18n import gettext as _


async def captcha_done(query: CallbackQuery, user: ChatModel, group: ChatModel, model: GreetingsModel, locale: str):
    if not isinstance(query.message, Message):
        raise SophieException("Invalid message type. Try initializing the captcha again.")

    captcha = EmojiCaptcha()
    captcha.show_emoji("✅")

    if not model.welcome_mute or not model.welcome_mute.time:
        raise ValueError("No welcome_mute")

    await ws_on_user_passed(user, group, model.welcome_mute)

    doc = Doc(_("You're all set, and can now participate in the conversation"))

    if model.welcome_mute.enabled:
        delta = convert_timedelta_or_str(model.welcome_mute.time)
        doc += Template(
            _("Due to group's security policy, you were restricted to send media for the next {time}"),
            time=format_timedelta(delta, locale=locale),
        )

    buttons = InlineKeyboardBuilder()

    if group.username:
        buttons.add(InlineKeyboardButton(text=f"👥 {_('Back to the group')}", url=f"https://t.me/{group.username}"))

    await send_captcha_message(query.message, captcha, str(doc), reply_markup=buttons.as_markup())

    # Send welcome message is enabled
    if not model.welcome_disabled:
        chat_rules = await RulesModel.get_rules(group.chat_id)
        saveable = model.note or get_default_welcome_message(bool(chat_rules))
        # If the message is in DM (user's chat), send welcome to group instead
        if query.message.chat.id == user.chat_id:
            # This is from join request, send to group
            from sophie_bot.services.bot import bot

            await bot.send_message(chat_id=group.chat_id, text=str(saveable.text or ""))
        else:
            return await send_welcome(query.message, saveable, False, chat_rules)
