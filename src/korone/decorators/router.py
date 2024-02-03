# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

from korone.decorators.factory import Factory


class RouterError(Exception):
    """
    An Router error.

    This exception is raised when a unsupported event is called by the :class:`Router`.
    """


class Router:
    """
    A class that represents a decorators router.

    This class is used to create a router for the decorators, it receives the
    name of the decorator as a parameter and returns the class that will be
    used to create the decorator.

    Attributes
    ----------
    message : Factory
        A Factory instance for creating message decorators.
    callback_query : Factory
        A Factory instance for creating callback query decorators.
    """

    __slots__ = ("callback_query", "message")

    def __init__(self) -> None:
        self.message = Factory("message")
        self.callback_query = Factory("callback_query")

    def __getattr__(self, name: str):
        raise RouterError(f"Event of type: '{name}' is not supported by the PyKorone.")
