# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from dataclasses import dataclass
from typing import Any

import polib
from babel.core import Locale
from babel.support import LazyProxy
from flag import flag
from hairydogm.i18n import I18n

from korone.utils.logging import log


@dataclass(frozen=True, slots=True)
class LocaleStats:
    """
    Represent the statistics of a locale.

    This class represents the statistics of a locale, such as the number of translated strings,
    untranslated strings, fuzzy strings, and the percentage of translated strings.
    """

    translated: int
    """The number of translated strings.

    :type: int
    """
    untranslated: int
    """The number of untranslated strings.

    :type: int
    """
    fuzzy: int
    """The number of fuzzy strings.

    :type: int
    """
    percent_translated: int
    """The percentage of translated strings.

    :type: int
    """


class I18nNew(I18n):
    """
    I18n class with additional functionality.

    This class extends the I18n class and provides additional functionality for
    handling internationalization.

    Parameters
    ----------
    *args : Any
        Positional arguments to be passed to the `I18n` class.
    **kwargs : Any
        Keyword arguments to be passed to the `I18n` class.
    """

    __slots__ = ("babels", "stats")

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.babels: dict[str, Locale] = {}
        self.stats: dict[str, LocaleStats | None] = {}

    def parse_stats(self, locale_code: str) -> LocaleStats | None:
        """
        Parse the statistics of a specific locale.

        Parses the statistics of a specific locale, such as the number of translated strings,

        Parameters
        ----------
        locale_code : str
            The code of the locale.

        Returns
        -------
        LocaleStats | None
            An instance of the `LocaleStats` class representing the statistics of the locale,
            or None if the locale file does not exist.
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
        """
        Retrieve the `Locale` instance for a specific locale code.

        This method retrieves the `Locale` instance for a specific locale code.

        Parameters
        ----------
        locale_code : str
            The code of the locale.

        Returns
        -------
        Locale
            An instance of the `Locale` class representing the locale.
        """
        if locale_code not in self.babels:
            self.babels[locale_code] = Locale.parse(locale_code)

        return self.babels[locale_code]

    @property
    def current_locale_babel(self) -> Locale:
        """
        Retrieve the `Locale` instance for the current locale.

        This property retrieves the `Locale` instance for the current locale.

        Returns
        -------
        Locale
            An instance of the `Locale` class representing the current locale.
        """
        return self.babel(self.ctx_locale.get())

    def locale_display(self, locale: Locale) -> str:
        """
        Return the display name of a specific locale.

        This method returns the display name of a specific locale.

        Parameters
        ----------
        locale : Locale
            An instance of the `Locale` class representing the locale.

        Returns
        -------
        str
            The display name of the locale.
        """
        default_lang = self.babel(self.default_locale)
        default_territory = default_lang.territory or "US"

        return f"{flag(locale.territory or default_territory)} {locale.display_name}"

    @property
    def current_locale_display(self) -> str:
        """
        Return the display name of the current locale.

        This property returns the display name of the current locale.

        Returns
        -------
        str
            The display name of the current locale.
        """
        return self.locale_display(self.current_locale_babel)

    def get_locale_stats(self, locale_code: str) -> LocaleStats | None:
        """
        Retrieve the statistics of a specific locale.

        This method retrieves the statistics of a specific locale, such as the number of translated
        strings, untranslated strings, fuzzy strings, and the percentage of translated strings.

        Parameters
        ----------
        locale_code : str
            The code of the locale.

        Returns
        -------
        LocaleStats | None
            An instance of the `LocaleStats` class representing the statistics of the locale,
            or None if the statistics cannot be parsed.
        """
        if locale_code in self.stats:
            return self.stats[locale_code]

        self.stats[locale_code] = self.parse_stats(locale_code)
        if not self.stats[locale_code]:
            log.warning("Can't parse stats for locale %s!", locale_code)

        return self.stats[locale_code]

    def get_current_locale_stats(self) -> LocaleStats | None:
        """
        Retrieve the statistics of the current locale.

        This method retrieves the statistics of the current locale, such as the number of
        translated strings, untranslated strings, fuzzy strings, and the percentage of translated
        strings.

        Returns
        -------
        LocaleStats | None
            An instance of the `LocaleStats` class representing the statistics of the current
            locale, or None if the statistics cannot be parsed.
        """
        return self.get_locale_stats(self.ctx_locale.get())

    def is_current_locale_default(self) -> bool:
        """
        Check if the current locale is the default locale.

        This method checks if the current locale is the default locale.

        Returns
        -------
        bool
            True if the current locale is the default locale, False otherwise.
        """
        return self.ctx_locale.get() == self.default_locale


def get_i18n() -> I18nNew:
    """
    Get the current I18n context.

    This function returns the current I18n context.

    Returns
    -------
    I18nNew
        The current I18n context.

    Raises
    ------
    LookupError
        If the I18n context is not set.
    """
    if (i18n := I18nNew.get_current(no_error=True)) is None:
        msg = "I18n context is not set"
        raise LookupError(msg)

    return i18n  # type: ignore


def gettext(*args: Any, **kwargs: Any) -> str:
    """
    Get the translated string for the given message.

    This function returns the translated string for the given message.

    Parameters
    ----------
    *args : Any
        Positional arguments for the message.
    **kwargs : Any
        Keyword arguments for the message.

    Returns
    -------
    str
        The translated string.
    """
    return get_i18n().gettext(*args, **kwargs)


def lazy_gettext(*args: Any, **kwargs: Any) -> LazyProxy:
    """
    Return a lazy proxy object for translating text.

    This can be used, for example, to implement lazy translation functions that delay the actual
    translation until the string is actually used. The rationale for such behavior is that the
    locale of the user may not always be available. In web applications, you only know the locale
    when processing a request.

    Parameters
    ----------
    *args : Any
        Positional arguments to be passed to the `gettext` function.
    **kwargs : Any
        Keyword arguments to be passed to the `gettext` function.

    Returns
    -------
    LazyProxy
        A lazy proxy object that represents the translated text.
    """
    return LazyProxy(gettext, *args, **kwargs, enable_cache=False)
