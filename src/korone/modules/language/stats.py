from stfu_tg import Code, Section, Template

from korone.utils.i18n import get_i18n
from korone.utils.i18n import gettext as _


def language_stats() -> Section:
    i18n = get_i18n()
    num_languages = len(i18n.available_locales)

    return Section(Template(_("{num} languages available."), num=Code(num_languages)), title=_("Language"))
