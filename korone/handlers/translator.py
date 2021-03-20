# This file is part of Korone (Telegram Bot)
# Copyright (C) 2021 AmanoTeam

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import html
from gpytranslate import Translator

from pyrogram import Client, filters
from pyrogram.types import Message

from korone.handlers.utilities import GROUP

tr = Translator()


# See https://cloud.google.com/translate/docs/languages
LANGUAGES = [
    "af",
    "sq",
    "am",
    "ar",
    "hy",
    "az",
    "eu",
    "be",
    "bn",
    "bs",
    "bg",
    "ca",
    "ceb",
    "zh",
    "co",
    "hr",
    "cs",
    "da",
    "nl",
    "en",
    "eo",
    "et",
    "fi",
    "fr",
    "fy",
    "gl",
    "ka",
    "de",
    "el",
    "gu",
    "ht",
    "ha",
    "haw",
    "he",
    "iw",
    "hi",
    "hmn",
    "hu",
    "is",
    "ig",
    "id",
    "ga",
    "it",
    "ja",
    "jv",
    "kn",
    "kk",
    "km",
    "rw",
    "ko",
    "ku",
    "ky",
    "lo",
    "la",
    "lv",
    "lt",
    "lb",
    "mk",
    "mg",
    "ms",
    "ml",
    "mt",
    "mi",
    "mr",
    "mn",
    "my",
    "ne",
    "no",
    "ny",
    "or",
    "ps",
    "fa",
    "pl",
    "pt",
    "pa",
    "ro",
    "ru",
    "sm",
    "gd",
    "sr",
    "st",
    "sn",
    "sd",
    "si",
    "sk",
    "sl",
    "so",
    "es",
    "su",
    "sw",
    "sv",
    "tl",
    "tg",
    "ta",
    "tt",
    "te",
    "th",
    "tr",
    "tk",
    "uk",
    "ur",
    "ug",
    "uz",
    "vi",
    "cy",
    "xh",
    "yi",
    "yo",
    "zu",
]


def get_tr_lang(text):
    if len(text.split()) > 0:
        lang = text.split()[0]
        if lang.split("-")[0] not in LANGUAGES:
            lang = "pt"
        if len(lang.split("-")) > 1:
            if lang.split("-")[1] not in LANGUAGES:
                lang = "pt"
    else:
        lang = "pt"
    return lang


@Client.on_message(filters.cmd(command="tr", action="Google Tradutor.", group=GROUP))
async def translate(c: Client, m: Message):
    text = m.text[4:]
    lang = get_tr_lang(text)

    text = text.replace(lang, "", 1).strip() if text.startswith(lang) else text

    if m.reply_to_message and not text:
        text = m.reply_to_message.text or m.reply_to_message.caption

    if not text:
        return await m.reply_text(
            "<b>Uso:</b> <code>/tr &lt;idioma&gt; texto para tradução</code> (Também pode ser usado em resposta a uma mensagem)."
        )

    sent = await m.reply_text("Traduzindo...")
    langs = {}

    if len(lang.split("-")) > 1:
        langs["sourcelang"] = lang.split("-")[0]
        langs["targetlang"] = lang.split("-")[1]
    else:
        langs["targetlang"] = lang

    trres = await tr(text, **langs)
    text = trres.text

    res = html.escape(text)
    await sent.edit_text(
        (
            "<b>Idioma:</b> {from_lang} -> {to_lang}\n<b>Tradução:</b> <code>{translation}</code>"
        ).format(from_lang=trres.lang, to_lang=langs["targetlang"], translation=res)
    )
