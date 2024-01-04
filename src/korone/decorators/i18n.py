# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

from collections.abc import Callable
from functools import wraps

from babel import Locale, UnknownLocaleError

from korone import i18n


def use_gettext(func: Callable) -> Callable:
    """
    Decorator for using gettext.

    This decorator sets the appropriate locale for the function based on the user's language code.
    If the user's locale is not available, it falls back to the default locale.

    Parameters
    ----------
    func : collections.abc.Callable
        The function to be decorated.

    Returns
    -------
    collections.abc.Callable
        The decorated function.

    Raises
    ------
    babel.UnknownLocaleError
        If the locale identifier is invalid.
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        message = args[2]
        try:
            locale = Locale.parse(message.from_user.language_code, sep="-")
            locale = f"{locale.language}_{locale.territory}"
            if locale not in i18n.available_locales:
                raise UnknownLocaleError("Invalid locale identifier")
        except UnknownLocaleError:
            locale = i18n.default_locale

        with i18n.context(), i18n.use_locale(locale):
            return await func(*args, **kwargs)

    return wrapper
