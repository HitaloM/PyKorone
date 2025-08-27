from __future__ import annotations

from io import BytesIO
from typing import ClassVar, Sequence

from PIL import ImageColor, ImageDraw
from PIL.Image import Image as PILImage, new
from PIL.ImageFont import FreeTypeFont, truetype


class EmojiBanner:
    """Simple emoji banner generator.

    Renders an emoji row and a text line on a soft gradient background.
    Output format: JPEG bytes.
    """

    # Canvas
    width: ClassVar[int] = 1000
    height: ClassVar[int] = 400

    # Default background gradient (pastel pink)
    background_color_start: ClassVar[str] = "#fff0f6"
    background_color_end: ClassVar[str] = "#ffd6e7"

    # Supported pastel themes
    pastel_themes: ClassVar[dict[str, tuple[str, str]]] = {
        "pink": ("#fff0f6", "#ffd6e7"),
        "red": ("#ffe7e7", "#ffc2c2"),
        "blue": ("#e6f4ff", "#cfeaff"),
        "green": ("#eafff1", "#c9ffde"),
    }

    # Fonts
    emoji_font_path: ClassVar[str] = "sophie_bot/fonts/joypixels.ttf"
    text_font_path: ClassVar[str] = "sophie_bot/fonts/text.ttf"

    # Defaults
    emoji_font_size: ClassVar[int] = 128
    text_font_size: ClassVar[int] = 48
    margin: ClassVar[int] = 28

    @classmethod
    def _gradient_background(cls, start_color: str, end_color: str) -> PILImage:
        img = new("RGB", (cls.width, cls.height))
        start_rgb = ImageColor.getrgb(start_color)
        end_rgb = ImageColor.getrgb(end_color)

        for y in range(cls.height):
            r = int(start_rgb[0] + (end_rgb[0] - start_rgb[0]) * (y / cls.height))
            g = int(start_rgb[1] + (end_rgb[1] - start_rgb[1]) * (y / cls.height))
            b = int(start_rgb[2] + (end_rgb[2] - start_rgb[2]) * (y / cls.height))
            for x in range(cls.width):
                img.putpixel((x, y), (r, g, b))
        return img

    @classmethod
    def _fit_font(cls, text: str, font_path: str, max_width: int, start_size: int) -> FreeTypeFont:
        size = max(int(start_size), 8)

        def load_font(s: int) -> FreeTypeFont:
            cur = max(int(s), 8)
            while True:
                try:
                    return truetype(font_path, cur)
                except OSError as e:
                    msg = str(e).lower()
                    # Bitmap emoji fonts (e.g., JoyPixels) only support discrete sizes
                    if "invalid pixel size" in msg:
                        if cur <= 8:
                            # Re-raise if even the minimum size is not supported
                            raise
                        cur -= 1
                        continue
                    # Propagate unrelated errors
                    raise

        # First, obtain a loadable font at or below the requested size
        font = load_font(size)

        # Downsize until it fits the width, reloading when size changes
        while True:
            bbox = font.getbbox(text)
            width = bbox[2] - bbox[0]
            if width <= max_width or size <= 8:
                return font
            new_size = max(8, int(size * 0.9))
            if new_size == size:
                new_size = size - 1
            size = new_size
            font = load_font(size)

    @classmethod
    def render(cls, emojis: Sequence[str] | str, text: str, color: str | None = None) -> bytes:
        """Render banner as JPEG bytes.

        :param emojis: sequence or string of emojis to render in a row
        :param text: text to draw below the emojis
        :param color: optional pastel theme name ("pink" | "red" | "blue" | "green")
        :return: jpeg bytes
        """
        if isinstance(emojis, str):
            emojis_text = emojis
        else:
            emojis_text = "".join(emojis)

        # Resolve gradient colors
        theme = (color or "").lower().strip() if color else ""
        if theme in cls.pastel_themes:
            start_c, end_c = cls.pastel_themes[theme]
        else:
            start_c, end_c = cls.background_color_start, cls.background_color_end

        image = cls._gradient_background(start_c, end_c)
        draw = ImageDraw.Draw(image)

        # Emoji line (centered horizontally at 40% height)
        emoji_font = cls._fit_font(emojis_text, cls.emoji_font_path, cls.width - 2 * cls.margin, cls.emoji_font_size)
        e_bbox = emoji_font.getbbox(emojis_text)
        e_w = e_bbox[2] - e_bbox[0]
        e_x = (cls.width - e_w) / 2
        e_y = int(cls.height * 0.22)
        draw.text((e_x, e_y), emojis_text, font=emoji_font, embedded_color=True)

        # Text (centered, fits one line)
        text = text.strip()
        text_font = cls._fit_font(text, cls.text_font_path, cls.width - 2 * cls.margin, cls.text_font_size)
        t_bbox = text_font.getbbox(text)
        t_w = t_bbox[2] - t_bbox[0]
        t_x = (cls.width - t_w) / 2
        t_y = int(cls.height * 0.62)
        draw.text((t_x, t_y), text, font=text_font, fill=(10, 10, 10))

        bio = BytesIO()
        image.save(bio, format="JPEG", quality=85)
        bio.seek(0)
        return bio.read()
