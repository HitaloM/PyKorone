# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from hydrogram.errors import PeerIdInvalid, UsernameInvalid, UsernameNotOccupied
from hydrogram.types import Message

from korone.utils.i18n import gettext as _


async def handle_error(message: Message, error: Exception) -> None:
    error_messages = {
        PeerIdInvalid: _("The provided user ID is invalid."),
        UsernameInvalid: _("The provided username is invalid."),
        UsernameNotOccupied: _("The provided username does not exist."),
        IndexError: _("No entity found with the provided identifier."),
        KeyError: _("Error accessing data."),
        ValueError: _("The provided value is not valid."),
    }
    for error_type, error_message in error_messages.items():
        if isinstance(error, error_type):
            await message.reply(error_message)
            break
    else:
        await message.reply(_("An unexpected error occurred."))
