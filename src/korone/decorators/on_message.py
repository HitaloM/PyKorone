# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

from collections.abc import Callable

from hydrogram.filters import Filter


def on_message(filters: Filter, group: int = 0) -> Callable:
    def decorator(func: Callable) -> Callable:
        func.on = "message"
        func.group = group
        func.filters = filters

        return func

    return decorator
