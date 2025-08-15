from io import BufferedReader, BytesIO
from typing import BinaryIO, Optional

from aiogram.types import Voice

from sophie_bot.services.ai import mistral_client
from sophie_bot.services.bot import bot


async def transform_voice_to_text(voice: Voice) -> str:
    downloaded_audio: Optional[BinaryIO] = await bot.download(voice.file_id)

    audio_bytes = BufferedReader(BytesIO(downloaded_audio.read()))  # type: ignore

    resp = await mistral_client.audio.transcriptions.complete_async(
        model="mistral-transcribe",
        file={
            "file_name": "audio.ogg",
            "content": audio_bytes,
            "content_type": "audio/ogg",
        },
    )

    respond: str = resp.text

    respond = respond.removesuffix("\n")

    return respond
