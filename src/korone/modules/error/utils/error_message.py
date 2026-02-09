from typing import TYPE_CHECKING

from stfu_tg import Doc, Italic, Title
from stfu_tg.doc import Element

from korone.utils.exception import KoroneError
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from korone.utils.i18n import LazyProxy


def get_error_message(exception: Exception) -> tuple[str | Element, ...]:
    if isinstance(exception, KoroneError):
        return exception.docs

    return tuple(x if isinstance(x, Element) else Italic(str(x)) for x in exception.args)


def generic_error_message(
    exception: Exception, *, title: str | LazyProxy | Element = l_("😞 I've got an error trying to process this update")
) -> dict[str, str]:
    return {"text": str(Doc(Title(title), *get_error_message(exception)))}
