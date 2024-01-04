# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

from .i18n import use_gettext
from .on_callback_query import on_callback_query
from .on_message import on_message

__all__ = (
    "use_gettext",
    "on_callback_query",
    "on_message",
)
