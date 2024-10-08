from dataclasses import dataclass
from pathlib import Path
from re import compile
from typing import Any, Callable, Optional

from aiogram.utils.i18n import I18n
from babel.core import Locale
from flag import flag

from sophie_bot.utils.logger import log

LANG_STATS_REGEX = compile(
    r"^(?:(\d+) translated message(?:s))(?:, )?(?:(\d+) fuzzy translation)?(?:," r" )?(?:(\d+) untranslated messages)?"
)


@dataclass
class LocaleStats:
    translated: int
    untranslated: int
    fuzzy: int

    def percent_translated(self) -> int:
        if self.translated == 0:
            # Avoid division by zero
            return 0
        return round(self.translated / (self.translated + self.fuzzy + self.untranslated) * 100)


class I18nNew(I18n):
    babels: dict[str, Locale] = {}
    stats: dict[str, Optional[LocaleStats]] = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        log.debug("Loading locales additional data...")
        for locale in self.locales.keys():
            babel = self.babel(locale)
            self.babels[locale] = babel
            self.stats[locale] = self.parse_stats(locale)
            if not self.stats[locale]:
                log.warning(f"Can't parse stats for locale {locale}!")

        # add en
        self.babels["en"] = self.babel("en_US")

    def parse_stats(self, locale_code: str) -> Optional[LocaleStats]:
        # Load a file
        path = Path(f"{self.path}/{locale_code}/stats.txt")
        if not path.exists():
            return None

        # Parse a file with regex
        with path.open() as file:
            match = LANG_STATS_REGEX.match(file.read())
            if match is None:
                return None

            # Parse a stats
            return LocaleStats(
                translated=int(match.group(1)),
                fuzzy=int(match.group(2)) if match.group(2) else 0,
                untranslated=int(match.group(3)) if match.group(3) else 0,
            )

    @staticmethod
    def babel(locale_code: str) -> Locale:
        return Locale.parse(locale_code)

    @property
    def current_locale_babel(self) -> Locale:
        return self.babels[self.ctx_locale.get()]

    def locale_display(self, locale: Locale) -> str:
        return f"{flag(locale.territory or '')} {locale.display_name}"

    @property
    def current_locale_display(self) -> str:
        return self.locale_display(self.current_locale_babel)

    def get_locale_stats(self, locale_code: str) -> Optional[LocaleStats]:
        return self.stats[locale_code]

    def get_current_locale_stats(self) -> Optional[LocaleStats]:
        return self.get_locale_stats(self.ctx_locale.get())

    def is_current_locale_default(self) -> bool:
        return self.ctx_locale.get() == self.default_locale


def get_i18n():
    i18n = I18nNew.get_current(no_error=True)
    if i18n is None:
        raise LookupError("I18n context is not set")
    return i18n


def gettext(*args: Any, **kwargs: Any) -> str:
    return get_i18n().gettext(*args, **kwargs)


class LazyProxy:
    def __init__(self, *items: str | Callable, **kwargs):
        self.items = items
        self.kwargs = kwargs

    def _i18n(self):
        if callable(self.items[0]):
            return str(self.items[0](**self.kwargs))
        return gettext(*self.items, **self.kwargs)

    def __str__(self):
        return self._i18n()

    def __eq__(self, other):
        text = self._i18n()
        return text == other

    def __contains__(self, item):
        return self._i18n() in item

    def __add__(self, other):
        return self._i18n() + other

    def __radd__(self, other):
        return other + self._i18n()


def lazy_plural_gettext(*args: Any, **kwargs: Any):
    return lambda n: get_i18n().gettext(*args, n=n, **kwargs)


lazy_gettext = LazyProxy
ngettext = gettext
lazy_ngettext = lazy_gettext
