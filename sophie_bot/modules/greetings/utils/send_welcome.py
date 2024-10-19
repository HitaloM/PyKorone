from typing import Optional

from aiogram.types import Message

from sophie_bot.db.models import RulesModel
from sophie_bot.db.models.notes import Saveable
from sophie_bot.modules.greetings.default_welcome import get_default_welcome_message
from sophie_bot.modules.notes.utils.send import saveable_to_text, send_saveable
from sophie_bot.utils.i18n import gettext as _


async def send_welcome(
    message: Message, saveable: Optional[Saveable], cleanservice_enabled: bool, chat_rules: Optional[RulesModel]
) -> Message:
    chat_id = message.chat.id

    additional_fillings = {"rules": saveable_to_text(chat_rules) if chat_rules else _("No chat rules, have fun!")}

    saveable = saveable or get_default_welcome_message(bool(chat_rules))

    return await send_saveable(
        message,
        chat_id,
        saveable,
        reply_to=message.message_id if not cleanservice_enabled else None,
        additional_fillings=additional_fillings,
    )
