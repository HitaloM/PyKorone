# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

from .on_callback_query import OnCallbackQuery
from .on_message import OnMessage


class Decorators(OnMessage, OnCallbackQuery):
    """
    Class that contains all decorators.

    This class is passed to PyKorone's client class, so that the user can
    use the decorators directly from the client instance.

    Examples
    --------
    >>> from korone.client import Korone

    >>> @Korone.on_message()
    ... async def on_message(client, message):
    ...     print(message)
    """

    pass


__all__ = ("Decorators",)
