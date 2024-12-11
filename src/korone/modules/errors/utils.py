# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from hydrogram.errors import ChannelPrivate, ChatWriteForbidden, FloodWait, MessageIdInvalid

IGNORED_EXCEPTIONS: tuple[type[Exception], ...] = (
    FloodWait,
    ChatWriteForbidden,
    ChannelPrivate,
    MessageIdInvalid,
)
