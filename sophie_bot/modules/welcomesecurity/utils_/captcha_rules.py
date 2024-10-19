from aiogram.types import InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from stfu_tg import Doc, Title

from sophie_bot.db.models import RulesModel
from sophie_bot.modules.welcomesecurity.callbacks import WelcomeSecurityRulesAgreeCB
from sophie_bot.modules.welcomesecurity.utils_.emoji_captcha import EmojiCaptcha
from sophie_bot.modules.welcomesecurity.utils_.send_captcha import send_captcha_message


async def captcha_send_rules(message: Message, rules: RulesModel):
    captcha = EmojiCaptcha()
    captcha.show_emoji("🪧")

    doc = Doc()
    doc += Title("Please read the chat rules")
    doc += rules.text

    buttons = InlineKeyboardBuilder()
    buttons.add(InlineKeyboardButton(text="✅ I agree", callback_data=WelcomeSecurityRulesAgreeCB().pack()))

    return await send_captcha_message(message, captcha, str(doc), reply_markup=buttons.as_markup())
