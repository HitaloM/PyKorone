from typing import Optional

from aiogram.types import Message, User

from sophie_bot.db.models import RulesModel
from sophie_bot.db.models.notes import Saveable, SaveableParseMode
from sophie_bot.modules.greetings.default_welcome import get_default_welcome_message
from sophie_bot.modules.notes.utils.send import send_saveable
from sophie_bot.modules.notes.utils.unparse_legacy import legacy_markdown_to_html
from sophie_bot.utils.i18n import gettext as _


async def send_welcome(
    message: Message,
    saveable: Optional[Saveable],
    cleanservice_enabled: bool,
    chat_rules: Optional[RulesModel],
    user: Optional[User] = None,
) -> Message:
    chat_id = message.chat.id

    rules_text = chat_rules.text or "" if chat_rules else _("No chat rules, have fun!")
    if chat_rules and chat_rules.parse_mode != SaveableParseMode.html:
        rules_text = legacy_markdown_to_html(rules_text)

    additional_fillings = {"rules": rules_text}

    saveable = saveable or get_default_welcome_message(bool(chat_rules))

    return await send_saveable(
        message,
        chat_id,
        saveable,
        reply_to=message.message_id if not cleanservice_enabled else None,
        additional_fillings=additional_fillings,
        user=user,
    )
