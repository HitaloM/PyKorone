# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from babel.support import LazyProxy

from korone.utils.i18n import lazy_gettext as _


class ModuleInfo:
    name: LazyProxy = _("Medias")
    summary: LazyProxy = _(
        "Some websites, when their links are shared on platforms like Telegram, do not generate "
        "a preview of the images or videos contained within. This can lead to a lack of context "
        "and visual appeal for the shared content.\n\nThis is where this module comes into play. "
        "It is designed to automatically detect the links of supported websites and upload the "
        "images and videos found within them. This ensures that a preview is always available, "
        "enhancing the user experience."
    )
    doc: LazyProxy = _(
        "Automatic media download is enabled for the following websites:\n"
        "- X (Twitter)\n"
        "- Instagram\n\n"
        "<b>Commands:</b>\n"
        "- /ytdl &lt;youtubelink&gt;: Download the YouTube video or audio from the given link."
    )
