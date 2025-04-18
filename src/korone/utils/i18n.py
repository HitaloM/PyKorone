# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

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
    """Statistics about a locale's translation state.

    Attributes:
        translated: Number of translated entries
        untranslated: Number of untranslated entries
        fuzzy: Number of fuzzy entries
        percent_translated: Percentage of translated entries
    """

    translated: int
    untranslated: int
    fuzzy: int
    percent_translated: int


class I18nNew(I18n):
    """Enhanced internationalization class with additional features.

    This class extends the base I18n class with capabilities for locale
    statistics tracking and display formatting.
    """

    __slots__ = ("babels", "stats")

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the I18nNew instance.

        Args:
            *args: Arguments to pass to the parent I18n class
            **kwargs: Keyword arguments to pass to the parent I18n class
        """
        super().__init__(*args, **kwargs)
        self.babels: dict[str, Locale] = {}
        self.stats: dict[str, LocaleStats | None] = {}

    def parse_stats(self, locale_code: str) -> LocaleStats | None:
        """Parse translation statistics for the specified locale.

        Args:
            locale_code: The locale code to parse statistics for

        Returns:
            LocaleStats object containing translation statistics, or None if unavailable
        """
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
        """Get a Babel Locale object for the specified locale code.

        Args:
            locale_code: The locale code to get a Babel Locale for

        Returns:
            Babel Locale object
        """
        if locale_code not in self.babels:
            self.babels[locale_code] = Locale.parse(locale_code)
        return self.babels[locale_code]

    @property
    def current_locale_babel(self) -> Locale:
        """Get the Babel Locale object for the current locale.

        Returns:
            Babel Locale object for the current context locale
        """
        return self.babel(self.ctx_locale.get())

    @staticmethod
    def locale_display(locale: Locale) -> str:
        """Format a locale for display with its territory flag.

        Args:
            locale: The Babel Locale object to format

        Returns:
            Formatted string with territory flag and locale display name
        """
        territory_flag = flag(locale.territory or "US")
        return f"{territory_flag} {locale.display_name}"

    @property
    def current_locale_display(self) -> str:
        """Get a formatted display string for the current locale.

        Returns:
            Formatted string with territory flag and locale display name
        """
        return self.locale_display(self.current_locale_babel)

    def get_locale_stats(self, locale_code: str) -> LocaleStats | None:
        """Get translation statistics for the specified locale.

        Args:
            locale_code: The locale code to get statistics for

        Returns:
            LocaleStats object containing translation statistics, or None if unavailable
        """
        if locale_code not in self.stats:
            self.stats[locale_code] = self.parse_stats(locale_code)
            if not self.stats[locale_code]:
                logger.warning("Can't parse stats for locale %s!", locale_code)
        return self.stats[locale_code]

    def get_current_locale_stats(self) -> LocaleStats | None:
        """Get translation statistics for the current locale.

        Returns:
            LocaleStats object containing translation statistics, or None if unavailable
        """
        return self.get_locale_stats(self.ctx_locale.get())

    def is_current_locale_default(self) -> bool:
        """Check if the current locale is the default locale.

        Returns:
            True if the current locale is the default locale, False otherwise
        """
        return self.ctx_locale.get() == self.default_locale


def get_i18n() -> I18nNew:
    """Get the current I18nNew instance from context.

    Returns:
        The current I18nNew instance

    Raises:
        LookupError: If the I18n context is not set
    """
    i18n = I18nNew.get_current(no_error=True)
    if i18n is None:
        msg = "I18n context is not set"
        raise LookupError(msg)
    return i18n  # type: ignore


def gettext(*args: Any, **kwargs: Any) -> str:
    """Get translated text from the current I18n instance.

    Args:
        *args: Arguments to pass to gettext
        **kwargs: Keyword arguments to pass to gettext

    Returns:
        Translated string
    """
    return get_i18n().gettext(*args, **kwargs)


def lazy_gettext(*args: Any, **kwargs: Any) -> LazyProxy:
    """Create a lazy proxy for gettext translation.

    The translation is evaluated only when the string is actually used.

    Args:
        *args: Arguments to pass to gettext
        **kwargs: Keyword arguments to pass to gettext

    Returns:
        LazyProxy that will evaluate to the translated string when needed
    """
    return LazyProxy(gettext, *args, **kwargs, enable_cache=False)


try:
    i18n = I18nNew(path=constants.BOT_ROOT_PATH / "locales")
except RuntimeError as e:
    logger.error("Failed to initialize I18n due to the following error: %s", e)
    sys.exit(1)
