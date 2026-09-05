from time import perf_counter
from typing import TYPE_CHECKING, Any

from aiogram import BaseMiddleware
from aiogram.dispatcher.flags import get_flag
from aiogram.types import Message, TelegramObject

from korone.args.base import PARSED_ARGUMENTS_KEY
from korone.modules.stickers.args import StickerStealPackArguments
from korone.modules.stickers.utils.pack import normalize_pack_title
from korone.modules.stickers.utils.processing import (
    StickerPackJob,
    StickerPackProcessingManager,
    StickerPackSubmission,
    sticker_pack_job_key,
)
from korone.modules.utils_.reply_or_edit import reply_message
from korone.utils.i18n import gettext as _

if TYPE_CHECKING:
    from korone.modules.stickers.utils.processing import StickerPackHandler

STICKER_PACK_PROCESSING_FLAG = "defer_sticker_pack_processing"


class StickerPackProcessingMiddleware(BaseMiddleware):
    def __init__(self, manager: StickerPackProcessingManager) -> None:
        self._manager = manager

    async def __call__(self, handler: StickerPackHandler, event: TelegramObject, data: dict[str, Any]) -> object:
        if not get_flag(data, STICKER_PACK_PROCESSING_FLAG) or not isinstance(event, Message):
            return await handler(event, data)

        arguments = data.get(PARSED_ARGUMENTS_KEY)
        source_sticker = event.reply_to_message.sticker if event.reply_to_message else None
        if not event.from_user or not isinstance(arguments, StickerStealPackArguments):
            return await handler(event, data)
        if not source_sticker or not source_sticker.set_name:
            return await handler(event, data)

        normalized_pack_title = normalize_pack_title(arguments.pack_name)
        job_key = sticker_pack_job_key(event.from_user.id, normalized_pack_title)
        detached_data = data.copy()

        submission = await self._manager.submit(
            StickerPackJob(
                handler=handler,
                event=event,
                data=detached_data,
                job_key=job_key,
                job_id=job_key.rsplit(":", maxsplit=1)[-1][:16],
                queued_at=perf_counter(),
                failure_text=str(_("Could not add any sticker from that pack.")),
            )
        )
        if submission is StickerPackSubmission.ACCEPTED:
            return None
        if submission is StickerPackSubmission.DUPLICATE:
            await reply_message(event, _("A copy of this sticker pack is already in progress."))
            return None

        await reply_message(event, _("Sticker pack processing is busy. Please try again later."))
        return None
