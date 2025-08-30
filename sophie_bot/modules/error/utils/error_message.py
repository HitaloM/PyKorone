import random
from typing import Optional, Any

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from stfu_tg import BlockQuote, Title, KeyValue, Code, Doc, Italic
from stfu_tg.doc import Element

from sophie_bot.config import CONFIG
from sophie_bot.modules.error.utils.haikus import HAIKUS
from sophie_bot.utils.exception import SophieException
from sophie_bot.utils.i18n import gettext as _, LazyProxy


def get_error_message(exception: Exception) -> tuple[str | Element, ...]:
    if isinstance(exception, SophieException):
        # It has 'docs' field
        return exception.docs

    # Return either as itself if the type is based on Core (STFU-able) or stringify as italic
    from stfu_tg.doc import Element

    return tuple(x if isinstance(x, Element) else Italic(str(x)) for x in exception.args)


def generic_error_message(
    exception: Exception,
    sentry_event_id: Optional[str],
    hide_contact: bool = False,
    title: str | LazyProxy | Element = _("😞 I've got an error trying to process this update"),
) -> dict[str, Any]:
    return {
        "text": str(
            Doc(
                Title(title),
                *get_error_message(exception),
                *(
                    ()
                    if isinstance(exception, SophieException)
                    else (
                        " ",
                        BlockQuote(Doc(*random.choice(HAIKUS))),
                    )
                ),
                *(
                    (
                        " ",
                        KeyValue(_("Reference ID"), Code(sentry_event_id)),
                    )
                    if sentry_event_id
                    else ()
                ),
            )
        ),
        "reply_markup": InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text=_("💬 Contact Sophie support"), url=CONFIG.support_link)]]
        )
        if not hide_contact
        else None,
    }
