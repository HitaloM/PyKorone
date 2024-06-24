# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from babel.support import LazyProxy

from korone.utils.i18n import lazy_gettext as _


class ModuleInfo:
    name: LazyProxy = _("Translator")
    summary: LazyProxy = _(
        "This module uses DeepL to translate text between languages. DeepL is "
        "a high-quality translation service that uses neural networks to provide "
        "accurate translations."
    )
    doc: LazyProxy = _(
        "<b>Commands:</b>\n"
        "- /tr &lt;source&gt;:&lt;target&gt; &lt;text&gt;: Translates text from the source "
        "language to the target language. Can also be used as reply to a message."
        "\n\n<b>Examples:</b>\n"
        "- Translate 'Hello, world!' from English to Spanish:\n"
        "-> <code>/tr en-es Hello, world!</code>\n\n"
        "- Translate 'Hallo, Welt!' from German to English:\n"
        "-> <code>/tr en Hallo, Welt!</code>\n\n"
        "<b>Notes:</b>\n"
        "<b>Supported Source Languages:</b>\n"
        "BG, CS, DA, DE, EL, EN, ES, ET, FI, FR, HU, ID, IT, JA, KO, LT, LV, NB, NL, PL, PT, RO, "
        "RU, SK, SL, SV, TR, UK, ZH\n\n"
        "<b>Supported Target Languages:</b>\n"
        "BG, CS, DA, DE, EL, EN, EN-GB, EN-US, ES, ET, FI, FR, HU, ID, IT, JA, KO, LT, LV, NB, "
        "NL, PL, PT, PT-BR, PT-PT, RO, RU, SK, SL, SV, TR, UK, ZH"
    )
