import random
from io import BytesIO
from typing import Any, ClassVar, Optional

import numpy as np
from PIL import ImageColor
from PIL.Image import Image, fromarray, new
from PIL.ImageDraw import Draw
from PIL.ImageFont import FreeTypeFont, truetype
from pydantic import BaseModel
from typing_extensions import Sequence

from sophie_bot.utils.logger import log


class EmojiCaptchaData(BaseModel):
    base_emoji: str
    back_row: list[str]
    front_row: list[str]

    def move_to_right(self):
        self.front_row = self.front_row[-1:] + self.front_row[:-1]

    def move_to_left(self):
        self.front_row = self.front_row[1:] + self.front_row[:1]

    @property
    def is_correct(self) -> bool:
        emoji_back_row_index = self.back_row.index(self.base_emoji)
        emoji_front_row_index = self.front_row.index(self.base_emoji)
        return emoji_back_row_index == emoji_front_row_index


class EmojiCaptcha(Image):
    # Settings
    width: ClassVar[int] = 700
    height: ClassVar[int] = 250
    allowed_emojis: ClassVar[tuple[str, ...]] = (
        "🍎",
        "🍇",
        "🍉",
        "🍒",
        "🍌",
        "🍍",
        "🥝",
        "🥭",
        "🥥",
    )
    emoji_font: ClassVar[str] = "sophie_bot/fonts/joypixels.ttf"
    emoji_size: ClassVar[int] = 109
    front_emojis_height: ClassVar[int] = 17
    background_color_start: ClassVar[str] = "#e6fffa"
    background_color_end: ClassVar[str] = "#c7fff4"
    draw_lines: bool = True
    lines_width: ClassVar[int] = 3
    lines_color: ClassVar[str] = "black"
    lines_margin: ClassVar[int] = 15
    emojis_font: ClassVar[FreeTypeFont] = truetype(emoji_font, emoji_size)

    data: EmojiCaptchaData

    def fill_background(self):
        # Convert HTML colors to RGB tuples
        start_rgb = ImageColor.getrgb(self.background_color_start)
        end_rgb = ImageColor.getrgb(self.background_color_end)

        # Iterate through each pixel in the image
        for y in range(self.height):
            # Calculate the color at this y position
            r = int(start_rgb[0] + (end_rgb[0] - start_rgb[0]) * (y / self.height))
            g = int(start_rgb[1] + (end_rgb[1] - start_rgb[1]) * (y / self.height))
            b = int(start_rgb[2] + (end_rgb[2] - start_rgb[2]) * (y / self.height))

            # Set the pixel color for the whole row
            for x in range(self.width):
                self.putpixel((x, y), (r, g, b))

    @classmethod
    def generate_emojis(cls, emojis: Sequence[str]) -> Image:
        emojis_text = "".join(emojis)

        image = new("RGBA", (cls.width, cls.height))
        draw = Draw(image)

        text_bbox = draw.textbbox((0, 0), emojis_text, font=cls.emojis_font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        text_x = (cls.width - text_width) / 2
        text_y = (cls.height - text_height) / 2

        draw.text((text_x, text_y), emojis_text, font=cls.emojis_font, embedded_color=True)

        return image

    def mix_emojis(self, back: Image, front: Image) -> Image:
        # Define the line height and calculate the center line

        upper_line_y = round(self.height / 2) - self.front_emojis_height - self.lines_width
        lower_line_y = round(self.height / 2) + self.front_emojis_height + self.lines_width

        # Create a new image for the line with the correct dimensions
        line_image = front.crop((0, upper_line_y, self.width, lower_line_y))
        back.paste(line_image, (0, upper_line_y))

        if self.draw_lines:
            draw = Draw(back)
            draw.line(
                [(0 + self.lines_margin, upper_line_y), (self.width - self.lines_margin, upper_line_y)],
                fill=self.lines_color,
                width=self.lines_width,
            )  # Top line
            draw.line(
                [(0 + self.lines_margin, lower_line_y), (self.width - self.lines_margin, lower_line_y)],
                fill=self.lines_color,
                width=self.lines_width,
            )  # Bottom line

        return back

    def add_noise(self):
        """Adds 20% RGB noise to the image."""

        # Convert the image to a NumPy array
        image_array = np.array(self)

        # Generate random noise (up to 20% of the max pixel value per channel)
        noise = np.random.randint(-51, 51, image_array.shape, dtype=np.int16)  # Noise range from -50 to +50

        # Add noise to the image
        noisy_image_array = image_array + noise

        # Ensure pixel values stay within the valid range [0, 255]
        noisy_image_array = np.clip(noisy_image_array, 0, 255)

        # Paste image
        self.paste(fromarray(noisy_image_array.astype(np.uint8)))

    def __init__(self, data: Optional[dict[str, Any]] = None):
        super().__init__()

        new_image = new("RGB", (self.width, self.height))
        self._mode = new_image.mode
        self._size = new_image._size
        self._im = new_image._im

        self.data = EmojiCaptchaData(**data) if data else self.generate_data()

    @property
    def image(self) -> bytes:
        self.fill_background()
        back_emojis = self.generate_emojis(self.data.back_row)
        front_emojis = self.generate_emojis(self.data.front_row)

        # Mix emojis
        mixed_emojis = self.mix_emojis(back_emojis, front_emojis)

        self.paste(im=mixed_emojis, mask=mixed_emojis)
        self.add_noise()

        byte_io = BytesIO()
        self.save(byte_io, format="JPEG", quality=60)
        byte_io.seek(0)
        return byte_io.read()

    @classmethod
    def generate_data(cls) -> EmojiCaptchaData:
        base_emoji = random.choice(cls.allowed_emojis)

        # Random emojis
        emojis_excluded_correct = [emoji for emoji in cls.allowed_emojis if emoji != base_emoji]
        back_row = random.sample(emojis_excluded_correct, 5)
        front_row = random.sample(emojis_excluded_correct, 5)

        back_index = random.randint(0, 4)
        back_row[back_index] = base_emoji

        front_index = random.randint(0, 4)
        front_row[front_index] = base_emoji

        if back_index == front_index:
            log.debug("Captcha: index collision detected")
            return cls.generate_data()

        return EmojiCaptchaData(
            base_emoji=base_emoji,
            back_row=back_row,
            front_row=front_row,
        )

    def show_emoji(self, emoji: str):
        self.draw_lines = False
        self.data = EmojiCaptchaData(
            base_emoji=emoji,
            back_row=[emoji],
            front_row=[emoji],
        )
