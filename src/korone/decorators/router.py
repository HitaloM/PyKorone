# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from .factory import Factory


class RouterError(Exception):
    pass


class Router:
    __slots__ = ("callback_query", "error", "message")

    def __init__(self) -> None:
        self.message = Factory("message")
        self.callback_query = Factory("callback_query")
        self.error = Factory("error")

    def __getattr__(self, name: str):
        msg = f"Event of type: '{name}' is not supported by the Korone."
        raise RouterError(msg)
