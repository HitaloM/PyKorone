# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2020-2022 Hitalo <https://github.com/HitaloSama>

import io

from PIL import Image


def sticker_color_sync(color: str) -> io.BytesIO:
    try:
        image = Image.new("RGBA", (512, 512), color)
    except BaseException:
        try:
            image = Image.new("RGBA", (512, 512), "#" + color)
        except BaseException:
            return

    image_stream = io.BytesIO()
    image_stream.name = "sticker.webp"
    image.save(image_stream, "WebP")
    image_stream.seek(0)

    return image_stream


def pokemon_image_sync(sprite_io: str) -> io.BytesIO:
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
