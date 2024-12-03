from aiogram.types import Message
from regex import regex

from sophie_bot.utils.exception import SophieException


def match_legacy_filter(message: Message, handler: str) -> bool:
    # Lower handler
    handler = handler.lower()

    message_text: str = (message.caption or message.text or "").lower()

    # Legacy regex support
    if handler.startswith("re:"):
        pattern = handler[3:]
        try:
            return bool(regex.search(pattern, message_text))
        except TimeoutError:
            raise SophieException(
                f'The regex in the filter with handler "{handler}" is taking too long to execute. Sophie will not function properly until it will be removed.'
            )

    if handler in message_text:
        return True

    return False
