from __future__ import annotations

from typing import TYPE_CHECKING, Any

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from stfu_tg import Code, Doc, Italic, KeyValue, Title
from stfu_tg.doc import Element

from korone.config import CONFIG
from korone.utils.exception import KoroneError
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from korone.utils.i18n import LazyProxy


def get_error_message(exception: Exception) -> tuple[str | Element, ...]:
    if isinstance(exception, KoroneError):
        return exception.docs

    if not exception.args:
        return (Italic(exception.__class__.__name__),)

    return tuple(x if isinstance(x, Element) else Italic(str(x)) for x in exception.args)


def generic_error_message(
    exception: Exception,
    sentry_event_id: str | None,
    *,
    hide_contact: bool = False,
    title: str | LazyProxy | Element = l_("😞 I've got an error trying to process this update"),
) -> dict[str, Any]:
    return {
        "text": str(
            Doc(
                Title(title),
                *get_error_message(exception),
                *((" ", KeyValue(_("Reference ID"), Code(sentry_event_id))) if sentry_event_id else ()),
            )
        ),
        "reply_markup": InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text=_("🐞 Open GitHub Issues"), url=CONFIG.github_issues)]]
        )
        if not hide_contact
        else None,
    }
