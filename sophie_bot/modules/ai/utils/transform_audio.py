from io import BufferedReader, BytesIO
from typing import BinaryIO, Optional

from aiogram.types import Voice

from sophie_bot import bot
from sophie_bot.services.ai import ai_client


async def transform_voice_to_text(voice: Voice) -> str:
    downloaded_audio: Optional[BinaryIO] = await bot.download(voice.file_id)

    audio_bytes = BufferedReader(BytesIO(downloaded_audio.read()))  # type: ignore

    respond: str = await ai_client.audio.transcriptions.create(
        file=("test.ogg", audio_bytes), model="whisper-1", response_format="text"
    )

    respond = respond.removesuffix("\n")

    return respond
