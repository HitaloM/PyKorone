# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from korone.modules.media_dl.utils.twitter.api import TweetMedia, TweetMediaVariants


def get_best_variant(media: TweetMedia) -> TweetMediaVariants | None:
    if not media.variants:
        return None

    return max(media.variants, key=lambda variant: variant.bitrate)
