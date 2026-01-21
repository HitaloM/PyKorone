from __future__ import annotations

import random
import time
from typing import Any, Awaitable, Callable, Dict, Optional, cast

from aiogram import BaseMiddleware
from aiogram.types import (
    CallbackQuery,
    ChatJoinRequest,
    ChatMemberUpdated,
    InlineQuery,
    Message,
    TelegramObject,
    Update,
)

from sophie_bot.metrics.prom import SophieMetrics
from sophie_bot.utils.logger import log


class MetricsMiddleware(BaseMiddleware):
    """Aiogram middleware for collecting Prometheus metrics"""

    def __init__(self, metrics: SophieMetrics, config: Any) -> None:
        self.metrics = metrics
        self.config = config
        super().__init__()

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        """Process update and collect metrics"""

        # Skip sampling if configured
        if self.config.metrics_sample_ratio < 1.0:
            if random.random() > self.config.metrics_sample_ratio:
                return await handler(event, data)

        # Extract update information
        update_info = self._extract_update_info(event, data)

        # Increment update counter
        self.metrics.updates_total.labels(
            update_type=update_info["update_type"],
            chat_type=update_info["chat_type"],
            transport=update_info["transport"],
        ).inc()

        # Increment message counter if it's a message
        if update_info["message_kind"]:
            self.metrics.messages_total.labels(message_kind=update_info["message_kind"]).inc()

        # Track inflight handlers
        self.metrics.inflight_handlers.inc()

        # Measure handler duration
        start_time = time.perf_counter()
        handler_name = self._get_handler_name(handler, event)

        try:
            result = await handler(event, data)
            return result

        except Exception as e:
            # Track handler errors
            exception_name = type(e).__name__
            self.metrics.handler_errors_total.labels(handler=handler_name, exception=exception_name).inc()

            log.debug("Handler error tracked", handler=handler_name, exception_type=exception_name, error=str(e))

            # Re-raise the exception
            raise

        finally:
            # Always decrement inflight handlers and record duration
            self.metrics.inflight_handlers.dec()

            # Record handler duration
            duration = time.perf_counter() - start_time
            self.metrics.handler_duration_seconds.labels(handler=handler_name).observe(duration)

    def _extract_update_info(self, event: TelegramObject, data: Dict[str, Any]) -> Dict[str, Optional[str]]:
        """Extract update information for labeling"""

        update_type = "unknown"
        chat_type = "unknown"
        transport = "polling"  # Default, can be overridden
        message_kind = None

        # Determine transport method
        if hasattr(data, "webhook_info") or data.get("webhook_info"):
            transport = "webhook"

        # Extract update type and chat type
        if isinstance(event, Update):
            # Determine update type
            if event.message:
                update_type = "message"
                message_kind = self._get_message_kind(event.message)
                chat_type = event.message.chat.type if event.message.chat else "unknown"
            elif event.edited_message:
                update_type = "edited_message"
                message_kind = self._get_message_kind(event.edited_message)
                chat_type = event.edited_message.chat.type if event.edited_message.chat else "unknown"
            elif event.callback_query:
                update_type = "callback_query"
                chat_type = (
                    event.callback_query.message.chat.type
                    if (event.callback_query.message and event.callback_query.message.chat)
                    else "unknown"
                )
            elif event.inline_query:
                update_type = "inline_query"
                chat_type = "inline"
            elif event.chat_member:
                update_type = "chat_member"
                chat_type = event.chat_member.chat.type if event.chat_member.chat else "unknown"
            elif event.my_chat_member:
                update_type = "my_chat_member"
                chat_type = event.my_chat_member.chat.type if event.my_chat_member.chat else "unknown"
            elif event.chat_join_request:
                update_type = "chat_join_request"
                chat_type = event.chat_join_request.chat.type if event.chat_join_request.chat else "unknown"
        elif isinstance(event, Message):
            update_type = "message"
            message_kind = self._get_message_kind(event)
            chat_type = event.chat.type if event.chat else "unknown"
        elif isinstance(event, CallbackQuery):
            update_type = "callback_query"
            chat_type = event.message.chat.type if (event.message and event.message.chat) else "unknown"
        elif isinstance(event, InlineQuery):
            update_type = "inline_query"
            chat_type = "inline"
        elif isinstance(event, ChatMemberUpdated):
            update_type = "chat_member"
            chat_type = event.chat.type if event.chat else "unknown"
        elif isinstance(event, ChatJoinRequest):
            update_type = "chat_join_request"
            chat_type = event.chat.type if event.chat else "unknown"

        return {
            "update_type": update_type,
            "chat_type": chat_type,
            "transport": transport,
            "message_kind": message_kind,
        }

    def _get_message_kind(self, message: Message) -> str:
        """Determine message kind for labeling"""
        if message.text:
            return "text"
        elif message.photo:
            return "photo"
        elif message.video:
            return "video"
        elif message.audio:
            return "audio"
        elif message.voice:
            return "voice"
        elif message.document:
            return "document"
        elif message.sticker:
            return "sticker"
        elif message.animation:
            return "animation"
        elif message.video_note:
            return "video_note"
        elif message.contact:
            return "contact"
        elif message.location:
            return "location"
        elif message.venue:
            return "venue"
        elif message.poll:
            return "poll"
        elif message.dice:
            return "dice"
        elif message.game:
            return "game"
        elif message.invoice:
            return "invoice"
        elif message.successful_payment:
            return "successful_payment"
        elif message.connected_website:
            return "connected_website"
        elif message.passport_data:
            return "passport_data"
        elif message.proximity_alert_triggered:
            return "proximity_alert"
        elif message.forum_topic_created:
            return "forum_topic_created"
        elif message.forum_topic_closed:
            return "forum_topic_closed"
        elif message.forum_topic_reopened:
            return "forum_topic_reopened"
        elif message.general_forum_topic_hidden:
            return "general_forum_topic_hidden"
        elif message.general_forum_topic_unhidden:
            return "general_forum_topic_unhidden"
        elif message.write_access_allowed:
            return "write_access_allowed"
        elif message.user_shared:
            return "user_shared"
        elif message.chat_shared:
            return "chat_shared"
        elif message.new_chat_members:
            return "new_chat_members"
        elif message.left_chat_member:
            return "left_chat_member"
        elif message.new_chat_title:
            return "new_chat_title"
        elif message.new_chat_photo:
            return "new_chat_photo"
        elif message.delete_chat_photo:
            return "delete_chat_photo"
        elif message.group_chat_created:
            return "group_chat_created"
        elif message.supergroup_chat_created:
            return "supergroup_chat_created"
        elif message.channel_chat_created:
            return "channel_chat_created"
        elif message.migrate_to_chat_id:
            return "migrate_to_chat_id"
        elif message.migrate_from_chat_id:
            return "migrate_from_chat_id"
        elif message.pinned_message:
            return "pinned_message"
        else:
            return "other"

    def _get_handler_name(self, handler: Callable, event: TelegramObject) -> str:
        """Extract handler name for labeling"""
        handler_name: str = "unknown"

        # Handle functools.partial objects (common with aiogram class-based handlers)
        if hasattr(handler, "func"):
            # This is likely a functools.partial object
            actual_func = getattr(handler, "func")
            if hasattr(actual_func, "__self__") and hasattr(actual_func, "__class__"):
                # This is a bound method, get the class name
                handler_name = actual_func.__self__.__class__.__name__
            elif hasattr(actual_func, "__name__"):
                handler_name = cast(str, getattr(actual_func, "__name__"))
            else:
                handler_name = str(actual_func)
        # Handle bound methods directly
        elif hasattr(handler, "__self__"):
            self_obj = getattr(handler, "__self__", None)
            if self_obj is not None and hasattr(self_obj, "__class__"):
                handler_name = self_obj.__class__.__name__
        # Handle regular functions
        elif hasattr(handler, "__name__"):
            handler_name = cast(str, getattr(handler, "__name__"))
        # Check for problematic string representations first (before class check)
        elif callable(handler):
            handler_str = str(handler)
            # Try to extract class name from string representation
            if "bound method" in handler_str and "of <" in handler_str:
                # Example: "<bound method AiPmStop.handle of <...>>"
                parts = handler_str.split(".")
                if len(parts) >= 2:
                    class_part = parts[-2].split()[-1]  # Get the class name
                    handler_name = class_part
            elif " object at " in handler_str:
                # Handle cases like "<sophie_bot.middlewares.connections.ConnectionsMiddleware object at 0x7fa6c518c380>"
                # Extract the class name before " object at"
                before_object = handler_str.split(" object at ")[0]
                if "." in before_object:
                    # Get the last part after the last dot (the class name)
                    handler_name = before_object.split(".")[-1]
                else:
                    # If no dots, remove angle brackets and use as is
                    handler_name = before_object.strip("<>")
            elif " " in handler_str:
                handler_name = handler_str.split(" ")[1]
            # Handle classes (if handler is a class itself) - moved after string parsing
            elif hasattr(handler, "__class__") and handler.__class__.__name__ != "function":
                handler_name = handler.__class__.__name__
            else:
                handler_name = handler_str

        # Clean up handler name to avoid high cardinality
        if "." in handler_name:
            handler_name = handler_name.split(".")[-1]
        if "<" in handler_name:
            handler_name = handler_name.replace("<", "").replace(">", "")
        if "'" in handler_name:
            handler_name = handler_name.replace("'", "")

        return handler_name[:50]  # Limit length to avoid cardinality issues
