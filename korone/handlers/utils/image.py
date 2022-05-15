# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2020-2022 Amano Team

import io

from PIL import Image

from korone.utils import aiowrap


@aiowrap
def stickcolorsync(color):
    try:
        image = Image.new("RGBA", (512, 512), color)
    except BaseException:
        try:
            image = Image.new("RGBA", (512, 512), "#" + color)
        except BaseException:
            return None

    image_stream = io.BytesIO()
    image_stream.name = "sticker.webp"
    image.save(image_stream, "WebP")
    image_stream.seek(0)

    return image_stream


@aiowrap
def pokemon_image_sync(sprite_io):
    sticker_image = Image.open(io.BytesIO(sprite_io))
    sticker_image = sticker_image.crop(sticker_image.getbbox())

    final_width = 512
    final_height = 512

    if sticker_image.width > sticker_image.height:
        final_height = 512 * (sticker_image.height / sticker_image.width)
    elif sticker_image.width < sticker_image.height:
        final_width = 512 * (sticker_image.width / sticker_image.height)

    sticker_image = sticker_image.resize(
        (int(final_width), int(final_height)), Image.NEAREST
    )
    sticker_io = io.BytesIO()
    sticker_image.save(sticker_io, "WebP", quality=99)
    sticker_io.seek(0)
    sticker_io.name = "sticker.webp"

    return sticker_io
