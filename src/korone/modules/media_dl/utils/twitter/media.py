# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from korone.modules.media_dl.utils.twitter.api import (
    TweetMedia,
    TweetMediaVariants,
    TwitterAPI,
)
from korone.modules.media_dl.utils.twitter.files import TwitterFileUtils


class TwitterMediaHandler:
    __slots__ = ("api", "files_utils")

    def __init__(self):
        self.api = TwitterAPI()
        self.files_utils = TwitterFileUtils()

    @staticmethod
    async def get_best_variant(media: TweetMedia) -> TweetMediaVariants | None:
        if not media.variants:
            return None

        return max(media.variants, key=lambda variant: variant.bitrate)

    async def process_video_media(self, media: TweetMedia | TweetMediaVariants) -> str:
        original_file = await self.files_utils.save_binary_io(media.binary_io)
        has_audio = await self.files_utils.video_has_audio(original_file)

        if has_audio:
            return original_file

        converted_file = await self.files_utils.add_silent_audio(original_file)
        await self.files_utils.delete_files([original_file])

        return converted_file
