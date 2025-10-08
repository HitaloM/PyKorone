# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

import sys

import logfire
from hydrogram import Client
from hydrogram.errors import ChatWriteForbidden
from hydrogram.types import (
    CallbackQuery,
    Chat,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQuery,
    Message,
    Update,
)
from opentelemetry.trace import format_trace_id

from korone import constants
from korone.decorators import router
from korone.modules.errors.utils import IGNORED_EXCEPTIONS, compute_error_signature, should_notify
from korone.utils.i18n import gettext as _
from korone.utils.logging import get_logger

logger = get_logger(__name__)


@router.error()
async def handle_error(client: Client, update: Update, exception: Exception) -> None:
    chat = get_chat_from_update(update)
    thread_id = get_thread_id_from_update(update)

    if await handle_ignored_exceptions(client, chat, exception):
        return

    if isinstance(exception, OSError):
        return

    sys_exception = await extract_exception_details(exception)
    if sys_exception is None:
        return

    trace_reference: str | None = None
    signature = compute_error_signature(sys_exception)

    with logfire.span(
        "Unhandled update exception",
        update_type=type(update).__name__,
        chat_id=chat.id if chat else None,
    ) as span:
        span.record_exception(sys_exception)
        span.set_attribute("otel.status_code", "ERROR")
        if chat:
            span.set_attribute("telegram.chat_type", chat.type)
        span_context = span.get_span_context()
        if span_context:
            trace_reference = format_trace_id(span_context.trace_id)

    await log_exception_details(
        trace_reference,
        signature,
        sys_exception,
        chat_id=chat.id if chat else None,
        update_type=type(update).__name__,
    )

    if not should_notify(signature):
        await logger.ainfo(
            "[ErrorHandler] Suppressing repeated notification",
            signature=signature,
        )
        return

    if not chat:
        await logger.aerror("[ErrorHandler] No chat for update", update=update)
        return

    if isinstance(update, InlineQuery):
        await logger.ainfo("[ErrorHandler] Inline query update, skipping notification")
        return

    await send_error_message(client, chat, trace_reference, signature, thread_id)


def get_chat_from_update(update: Update) -> Chat | None:
    if isinstance(update, Message):
        return update.chat
    return update.message.chat if isinstance(update, CallbackQuery) else None


def get_thread_id_from_update(update: Update) -> int | None:
    if isinstance(update, Message):
        return update.message_thread_id
    if isinstance(update, CallbackQuery) and update.message:
        return update.message.message_thread_id
    return None


async def extract_exception_details(exception: Exception) -> BaseException | None:
    etype, value, tb = sys.exc_info()
    sys_exception = sys.exception()

    if not (etype and value and tb):
        await logger.aerror("[ErrorHandler] Missing exception info", exception=exception)
        return None

    if not isinstance(sys_exception, BaseException):
        await logger.aerror("[ErrorHandler] Missing sys.exception", exception=exception)
        return None

    if sys_exception is not exception:
        await logger.aerror(
            "[ErrorHandler] Mismatched active exception",
            handler_exception=repr(exception),
            sys_exception=repr(sys_exception),
        )

    return sys_exception


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
    trace_reference: str | None,
    signature: str,
    sys_exception: BaseException,
    *,
    chat_id: int | None,
    update_type: str,
) -> None:
    log_kwargs: dict[str, object] = {"signature": signature, "update_type": update_type}
    if chat_id is not None:
        log_kwargs["chat_id"] = chat_id
    if trace_reference:
        log_kwargs["trace_reference"] = trace_reference

    await logger.aerror(
        "[ErrorHandler] Unhandled update exception",
        exc_info=(type(sys_exception), sys_exception, sys_exception.__traceback__),
        **log_kwargs,
    )


async def send_error_message(
    client: Client,
    chat: Chat,
    trace_reference: str | None,
    signature: str,
    message_thread_id: int | None,
) -> None:
    text = _("An unexpected error occurred while processing this update! :/")
    if trace_reference:
        text += _("\nTrace ID: {id}").format(id=trace_reference)
    if signature:
        signature_fragment = signature[:12]
        text += _("\nError signature: {signature}").format(signature=signature_fragment)

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                text=_("🐞 Report This Error"), url=f"{constants.GITHUB_URL}/issues"
            )
        ]
    ])
    if message_thread_id is not None:
        await client.send_message(
            chat.id,
            text=text,
            reply_markup=keyboard,
            message_thread_id=message_thread_id,
        )
        return

    await client.send_message(chat.id, text=text, reply_markup=keyboard)
