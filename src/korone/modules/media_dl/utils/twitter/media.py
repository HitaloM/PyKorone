# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from korone.modules.media_dl.utils.twitter.api import TweetMedia, TweetMediaVariants
from korone.modules.media_dl.utils.twitter.files import (
    add_silent_audio,
    delete_files,
    save_binary_io,
    video_has_audio,
)


def get_best_variant(media: TweetMedia) -> TweetMediaVariants | None:
    if not media.variants:
        return None

    return max(media.variants, key=lambda variant: variant.bitrate)


async def process_video_media(media: TweetMedia | TweetMediaVariants) -> str:
    original_file = await save_binary_io(media.binary_io)
    has_audio = await video_has_audio(original_file)

    if has_audio:
        return original_file

    converted_file = await add_silent_audio(original_file)
    await delete_files([original_file])

    return converted_file
