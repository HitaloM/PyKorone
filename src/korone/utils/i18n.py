# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import sys
from dataclasses import dataclass
from typing import Any

import polib
from babel.core import Locale
from babel.support import LazyProxy
from flag import flag
from hairydogm.i18n import I18n

from korone import constants

from .logging import logger


@dataclass(frozen=True, slots=True)
class LocaleStats:
    translated: int
    untranslated: int
    fuzzy: int
    percent_translated: int


class I18nNew(I18n):
    __slots__ = ("babels", "stats")

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.babels: dict[str, Locale] = {}
        self.stats: dict[str, LocaleStats | None] = {}

    def parse_stats(self, locale_code: str) -> LocaleStats | None:
        locale_path = self.path / locale_code / "LC_MESSAGES" / f"{self.domain}.po"
        if not locale_path.exists():
            return None

        po = polib.pofile(locale_path.as_posix())
        return LocaleStats(
            translated=len(po.translated_entries()),
            untranslated=len(po.untranslated_entries()),
            fuzzy=len(po.fuzzy_entries()),
            percent_translated=po.percent_translated(),
        )

    def babel(self, locale_code: str) -> Locale:
        if locale_code not in self.babels:
            self.babels[locale_code] = Locale.parse(locale_code)
        return self.babels[locale_code]

    @property
    def current_locale_babel(self) -> Locale:
        return self.babel(self.ctx_locale.get())

    @staticmethod
    def locale_display(locale: Locale) -> str:
        territory_flag = flag(locale.territory or "US")
        return f"{territory_flag} {locale.display_name}"

    @property
    def current_locale_display(self) -> str:
        return self.locale_display(self.current_locale_babel)

    def get_locale_stats(self, locale_code: str) -> LocaleStats | None:
        if locale_code not in self.stats:
            self.stats[locale_code] = self.parse_stats(locale_code)
            if not self.stats[locale_code]:
                logger.warning("Can't parse stats for locale %s!", locale_code)
        return self.stats[locale_code]

    def get_current_locale_stats(self) -> LocaleStats | None:
        return self.get_locale_stats(self.ctx_locale.get())

    def is_current_locale_default(self) -> bool:
        return self.ctx_locale.get() == self.default_locale


def get_i18n() -> I18nNew:
    i18n = I18nNew.get_current(no_error=True)
    if i18n is None:
        msg = "I18n context is not set"
        raise LookupError(msg)
    return i18n  # type: ignore


def gettext(*args: Any, **kwargs: Any) -> str:
    return get_i18n().gettext(*args, **kwargs)


def lazy_gettext(*args: Any, **kwargs: Any) -> LazyProxy:
    return LazyProxy(gettext, *args, **kwargs, enable_cache=False)


try:
    i18n = I18nNew(path=constants.BOT_ROOT_PATH / "locales")
except RuntimeError as e:
    logger.error(
        "Failed to initialize I18n due to the following error: %s. "
        "This usually happens when the locale files are not compiled. "
        "Please compile the locales using 'rye run compile-locales' and try again.",
        e,
    )
    sys.exit(1)
