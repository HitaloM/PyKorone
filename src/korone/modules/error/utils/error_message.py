from typing import Any

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from korone.config import CONFIG
from korone.ui import Bold, Code, Italic, Renderable, Text, UIExpression, column, field
from korone.ui.rendering import text_kwargs
from korone.utils.exception import KoroneError
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_


def get_error_message(exception: Exception) -> tuple[Renderable, ...]:
    if isinstance(exception, KoroneError):
        if exception.docs:
            return exception.docs
        return (Italic(exception.__class__.__name__),)

    if not exception.args:
        return (Italic(exception.__class__.__name__),)

    return tuple(x if isinstance(x, (UIExpression, Text, str, int, float)) else Italic(str(x)) for x in exception.args)


def generic_error_message(
    exception: Exception,
    sentry_event_id: str | None,
    *,
    hide_contact: bool = False,
    title: Renderable = l_("😞 I've got an error trying to process this update"),
) -> dict[str, Any]:
    content = column(
        Bold(title),
        *get_error_message(exception),
        *((" ", field(_("Reference ID"), Code(sentry_event_id))) if sentry_event_id else ()),
    )
    return text_kwargs(
        content,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text=_("🐞 Open GitHub Issues"), url=CONFIG.github_issues)]]
        )
        if not hide_contact
        else None,
    )
