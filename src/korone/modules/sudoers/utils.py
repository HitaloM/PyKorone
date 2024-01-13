# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

import io
import re

from hydrogram.types import Message


def build_text(output: str) -> str:
    output = re.sub(f'([{re.escape("```")}])', r"\\\1", output)

    return f"```bash\n{output}\n```"


async def generate_document(output: str, message: Message):
    with io.BytesIO(str.encode(output)) as file:
        file.name = "output.txt"
        caption = "Output is too large to be sent as a text message."
        await message.reply_document(file, caption=caption)
