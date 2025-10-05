# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

import sys
from traceback import format_exception

import logfire
from hydrogram import Client
from hydrogram.errors import ChatWriteForbidden
from hydrogram.types import (
    CallbackQuery,
    Chat,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    Update,
)
from opentelemetry.trace import format_trace_id

from korone import constants
from korone.decorators import router
from korone.modules.errors.utils import IGNORED_EXCEPTIONS
from korone.utils.i18n import gettext as _
from korone.utils.logging import get_logger

logger = get_logger(__name__)


@router.error()
async def handle_error(client: Client, update: Update, exception: Exception) -> None:
    chat = get_chat_from_update(update)

    if await handle_ignored_exceptions(client, chat, exception):
        return

    if isinstance(exception, OSError):
        return

    etype, value, tb = sys.exc_info()
    if not (etype and value and tb):
        await logger.aerror("[ErrorHandler] Missing exception info", exception=exception)
        return

    formatted_exception = format_exception(etype, value, tb)
    trace_reference: str | None = None

    with logfire.span(
        "Unhandled update exception",
        update_type=type(update).__name__,
        chat_id=chat.id if chat else None,
    ) as span:
        span.record_exception(exception)
        if chat:
            span.set_attribute("telegram.chat_type", chat.type)
        span_context = span.get_span_context()
        if span_context:
            trace_reference = format_trace_id(span_context.trace_id)

    await log_exception_details(formatted_exception, trace_reference)

    if not chat:
        await logger.aerror("[ErrorHandler] No chat for update", update=update)
        return

    await send_error_message(client, chat, trace_reference)


def get_chat_from_update(update: Update) -> Chat | None:
    if isinstance(update, Message):
        return update.chat
    return update.message.chat if isinstance(update, CallbackQuery) else None


async def handle_ignored_exceptions(
    client: Client, chat: Chat | None, exception: Exception
) -> bool:
    if isinstance(exception, IGNORED_EXCEPTIONS):
        if isinstance(exception, ChatWriteForbidden) and chat:
            await logger.aerror(
                "[ErrorHandler] ChatWriteForbidden exception occurred, leaving chat",
                chat_title=chat.title,
                chat_id=chat.id,
            )
            await client.leave_chat(chat.id)
        return True
    return False


async def log_exception_details(
    formatted_exception: list[str], trace_reference: str | None
) -> None:
    await logger.aerror("".join(formatted_exception))
    await logger.aerror("[ErrorHandler] Additional error data", trace_reference=trace_reference)


async def send_error_message(client: Client, chat: Chat, trace_reference: str | None) -> None:
    text = _("An unexpected error occurred while processing this update! :/")
    if trace_reference:
        text += _("\nTrace ID: {id}").format(id=trace_reference)

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                text=_("🐞 Report This Error"), url=f"{constants.GITHUB_URL}/issues"
            )
        ]
    ])
    await client.send_message(chat.id, text=text, reply_markup=keyboard)
