# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import sys
from traceback import format_exception

from hydrogram import Client
from hydrogram.errors import ChatWriteForbidden
from hydrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    Update,
)
from sentry_sdk import capture_exception

from korone.decorators import router
from korone.modules.errors.utils import IGNORED_EXCEPTIONS
from korone.utils.i18n import gettext as _
from korone.utils.logging import logger


@router.error()
async def handle_error(client: Client, update: Update, exception: Exception) -> None:
    chat = None
    if isinstance(update, Message):
        chat = update.chat
    elif isinstance(update, CallbackQuery):
        chat = update.message.chat

    if isinstance(exception, IGNORED_EXCEPTIONS):
        if isinstance(exception, ChatWriteForbidden) and chat:
            await logger.aerror(
                "[ErrorHandler] ChatWriteForbidden exception occurred, leaving chat",
                chat_title=chat.title,
                chat_id=chat.id,
            )
            await client.leave_chat(chat.id)
        return

    if isinstance(exception, OSError):
        return

    etype, value, tb = sys.exc_info()
    if not (etype and value and tb):
        await logger.aerror(
            "[ErrorHandler] Failed to retrieve exception information", exception=exception
        )
        return

    sentry_event_id = capture_exception(exception)
    formatted_exception = format_exception(etype, value, tb)
    await logger.aerror("".join(formatted_exception))
    await logger.aerror("[ErrorHandler] Additional error data", sentry_event_id=sentry_event_id)

    if not chat:
        await logger.aerror("[ErrorHandler] Unhandled update type", update=update)
        return

    text = _("An unexpected error occurred while processing this update! :/")
    if sentry_event_id:
        text += _("\nReference ID: {id}").format(id=sentry_event_id)

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                text=_("🐞 Report This Error"), url="https://github.com/HitaloM/PyKorone/issues"
            )
        ]
    ])
    await client.send_message(chat.id, text=text, reply_markup=keyboard)
