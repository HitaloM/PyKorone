# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from hydrogram.enums import MessageMediaType

SUPPORTED_CONTENTS = {
    MessageMediaType.PHOTO: "photo",
    MessageMediaType.VIDEO: "video",
    MessageMediaType.AUDIO: "audio",
    MessageMediaType.VOICE: "voice",
    MessageMediaType.DOCUMENT: "document",
    MessageMediaType.STICKER: "sticker",
    MessageMediaType.ANIMATION: "animation",
}
