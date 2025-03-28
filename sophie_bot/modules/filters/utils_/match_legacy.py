from aiogram.types import Message
from normality import normalize
from regex import regex

from sophie_bot.utils.exception import SophieException
from sophie_bot.utils.logger import log


def match_regex_handler(message_text: str, pattern: str) -> bool:
    """Match message text against a regex pattern."""
    try:
        return bool(regex.search(pattern, message_text))
    except TimeoutError:
        raise SophieException(
            f'The regex in the filter with pattern "{pattern}" is taking too long to execute. '
            f"Sophie will not function properly until it will be removed."
        )


def match_exact_handler(message_text: str, text: str) -> bool:
    """Match message text exactly against the provided text."""
    # For exact match, we need to compare the whole strings
    return message_text == text


def match_contains_handler(message_text: str, text: str) -> bool:
    """Check if message text contains the specified text."""
    normalized_text = normalize(text)
    if not normalized_text:
        return False
    return normalized_text in message_text


def match_legacy_handler(message: Message, handler: str) -> bool:
    """Match a message against different types of handlers (regex, exact, contains)."""
    if not (message_text := message.caption or message.text or ""):
        return False

    # Legacy regex support
    if handler.startswith("re:"):
        log.debug(f"match_legacy_handler: regex: {handler}")
        pattern = handler[3:]
        return match_regex_handler(message_text, pattern)

    # Exact text match
    if handler.startswith("exact:"):
        log.debug(f"match_legacy_handler: exact: {handler}")
        text = handler[6:]
        return match_exact_handler(message_text, text)

    # Contains text match (default behavior)
    log.debug(f"match_legacy_handler: contains: {handler}")
    return match_contains_handler(message_text, handler)
