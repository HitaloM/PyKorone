import random
from typing import Any

from stfu_tg import BlockQuote, Doc, Italic, Title
from stfu_tg.doc import Element

from korone.modules.error.utils.haikus import HAIKUS
from korone.utils.exception import KoroneException
from korone.utils.i18n import LazyProxy
from korone.utils.i18n import lazy_gettext as l_


def get_error_message(exception: Exception) -> tuple[str | Element, ...]:
    if isinstance(exception, KoroneException):
        return exception.docs

    from stfu_tg.doc import Element

    return tuple(x if isinstance(x, Element) else Italic(str(x)) for x in exception.args)


def generic_error_message(
    exception: Exception,
    hide_contact: bool = False,
    title: str | LazyProxy | Element = l_("😞 I've got an error trying to process this update"),
) -> dict[str, Any]:
    return {
        "text": str(
            Doc(
                Title(title),
                *get_error_message(exception),
                *(() if isinstance(exception, KoroneException) else (" ", BlockQuote(Doc(*random.choice(HAIKUS))))),
            )
        )
    }
