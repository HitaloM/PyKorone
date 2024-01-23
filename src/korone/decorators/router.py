# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

from .factory import Factory


class Router:
    """
    A class that represents a decorators router.

    This class is used to create a router for the decorators, it receives the
    name of the decorator as a parameter and returns the class that will be
    used to create the decorator.

    Attributes
    ----------
    message: Factory
        A factory that creates a decorator for the message event.
    callback_query: Factory
        A factory that creates a decorator for the callback_query event.
    """

    def __init__(self) -> None:
        self.message = Factory("message")
        self.callback_query = Factory("callback_query")
