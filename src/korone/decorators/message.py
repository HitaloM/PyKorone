# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

from collections.abc import Callable

from hydrogram.filters import Filter
from hydrogram.handlers import MessageHandler

from korone.config import ConfigManager


def on_message(filters: Filter, group: int = 0, sudoers_only: bool = True) -> Callable:
    def decorator(func: Callable) -> Callable:
        func.group = group

        func.filters = filters
        if sudoers_only:
            config = ConfigManager()
            func.filters = filters & config.get("korone", "SUDOERS")

        if not hasattr(func, "handlers"):
            func.handlers = []

        func.handlers.append(
            (
                MessageHandler(func, filters),
                group,
            )
        )

        return func

    return decorator
