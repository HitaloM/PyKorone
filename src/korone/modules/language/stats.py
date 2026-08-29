from korone.ui import Code, UIExpression, field, section
from korone.utils.i18n import get_i18n


def language_stats() -> UIExpression:
    i18n = get_i18n()
    num_languages = len(i18n.available_locales)

    return section("Language", field("Languages available", Code(num_languages)))
