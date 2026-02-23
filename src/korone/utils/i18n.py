from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, cast

import polib
from aiogram.utils.i18n import I18n
from babel.core import Locale
from babel.support import LazyProxy as BabelLazyProxy
from flag import flag

from korone.config import CONFIG
from korone.logger import get_logger

if TYPE_CHECKING:
    from collections.abc import Callable

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class LocaleStats:
    translated: int
    untranslated: int
    fuzzy: int

    def percent_translated(self) -> int:
        if self.translated == 0:
            return 0
        return round(self.translated / (self.translated + self.fuzzy + self.untranslated) * 100)


class I18nNew(I18n):
    babels: ClassVar[dict[str, Locale]] = {}
    stats: ClassVar[dict[str, LocaleStats | None]] = {}

    def __init__(self, *, path: str | Path, default_locale: str = "en", domain: str = "messages") -> None:
        super().__init__(path=path, default_locale=default_locale, domain=domain)

        logger.debug("Loading locales additional data...")
        for locale in self.locales:
            babel = self.babel(locale)
            self.babels[locale] = babel
            self.stats[locale] = self.parse_stats(locale)
            if not self.stats[locale]:
                logger.debug("Can't parse stats for locale", locale=locale)

        self.babels["en"] = self.babel("en_US")

    def parse_stats(self, locale_code: str) -> LocaleStats | None:
        path = Path(self.path) / locale_code / "LC_MESSAGES" / f"{self.domain}.po"
        if not path.exists():
            return None

        try:
            po = polib.pofile(path)
        except (OSError, UnicodeDecodeError, polib.errors.POFileError) as exc:  # type: ignore[attr-defined]
            logger.debug("Can't parse stats for locale", locale=locale_code, error=str(exc))
            return None

        return LocaleStats(
            translated=len(po.translated_entries()),
            fuzzy=len(po.fuzzy_entries()),
            untranslated=len(po.untranslated_entries()),
        )

    @staticmethod
    def babel(locale_code: str) -> Locale:
        return Locale.parse(locale_code)

    @property
    def current_locale_babel(self) -> Locale:
        return self.babels[self.ctx_locale.get()]

    @staticmethod
    def locale_display(locale: Locale) -> str:
        return f"{flag(locale.territory or '')} {locale.display_name}"

    @property
    def current_locale_display(self) -> str:
        return self.locale_display(self.current_locale_babel)

    def get_locale_stats(self, locale_code: str) -> LocaleStats | None:
        return self.stats[locale_code]

    def get_current_locale_stats(self) -> LocaleStats | None:
        return self.get_locale_stats(self.ctx_locale.get())

    def is_current_locale_default(self) -> bool:
        return self.ctx_locale.get() == self.default_locale

    @staticmethod
    def to_iso_639_1(lang_code: str) -> str:
        return lang_code.split("_", 1)[0]

    @property
    def locales_iso_639_1(self) -> tuple[str, ...]:
        return tuple(self.to_iso_639_1(lang_code) for lang_code in self.available_locales)

    @property
    def current_locale_iso_639_1(self) -> str:
        return self.to_iso_639_1(self.current_locale)


def get_i18n() -> I18nNew:
    i18n = I18nNew.get_current(no_error=True)
    if i18n is None:
        msg = "I18n context is not set"
        raise LookupError(msg)
    return cast("I18nNew", i18n)


def gettext(message: str, plural: str | None = None, n: int = 1, locale: str | None = None) -> str:
    return get_i18n().gettext(message, plural=plural, n=n, locale=locale)


class LazyProxy(BabelLazyProxy):
    __isabstractmethod__: bool = False

    def __init__(self, *items: str | Callable, enable_cache: bool = True, **kwargs: str | float | bool) -> None:
        if callable(items[0]):
            func = items[0]
            args = items[1:]
        else:
            func = gettext
            args = items
        super().__init__(func, *args, enable_cache=enable_cache, **kwargs)


def lazy_plural_gettext(message: str, plural: str | None = None) -> Callable[[int], str]:
    def _inner(n: int) -> str:
        return get_i18n().gettext(message, plural=plural, n=n)

    return _inner


lazy_gettext = LazyProxy
ngettext = gettext
lazy_ngettext = lazy_gettext


i18n = I18nNew(path="locales", domain="korone", default_locale=CONFIG.default_locale)
i18n.set_current(i18n)
