# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

from __future__ import annotations

from typing import Self

from .factory import Factory


class RouterError(Exception):
    pass


class Router:
    __slots__ = ("callback_query", "error", "message")

    def __init__(self) -> None:
        self.message: Factory = Factory("message")
        self.callback_query: Factory = Factory("callback_query")
        self.error: Factory = Factory("error")

    def __getattr__(self, name: str) -> Self:
        msg = f"Event of type '{name}' is not supported by Korone."
        raise RouterError(msg)
