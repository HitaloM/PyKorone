from time import perf_counter
from typing import TYPE_CHECKING, Any

from aiogram import BaseMiddleware
from aiogram.dispatcher.flags import get_flag

from korone.modules.medias.utils.processing import MediaHandler, MediaJob, MediaProcessingManager, media_source_id

if TYPE_CHECKING:
    from aiogram.types import TelegramObject

MEDIA_PROCESSING_FLAG = "defer_media_processing"


class MediaProcessingMiddleware(BaseMiddleware):
    def __init__(self, manager: MediaProcessingManager) -> None:
        self._manager = manager

    async def __call__(self, handler: MediaHandler, event: TelegramObject, data: dict[str, Any]) -> object:
        if not get_flag(data, MEDIA_PROCESSING_FLAG):
            return await handler(event, data)

        match data.get("media_urls"):
            case [str() as source_url, *_]:
                pass
            case _:
                return await handler(event, data)

        handler_object = data.get("handler")
        callback = getattr(handler_object, "callback", None)
        handler_name = getattr(callback, "__name__", type(callback).__name__)

        detached_data = data.copy()
        detached_data.pop("state", None)
        detached_data.pop("raw_state", None)
        detached_data.pop("fsm_storage", None)

        job = MediaJob(
            handler=handler,
            event=event,
            data=detached_data,
            handler_name=handler_name,
            source_url=source_url,
            source_id=media_source_id(source_url),
            queued_at=perf_counter(),
        )
        await self._manager.submit(job)
        return None
