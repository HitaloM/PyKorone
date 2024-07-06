# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from babel.support import LazyProxy

from korone.utils.i18n import lazy_gettext as _


class ModuleInfo:
    name: LazyProxy = _("Medias")
    summary: LazyProxy = _(
        "Some websites, when their links are shared on Telegram, do not display a preview of the "
        "content. This module solves this problem by automatically downloading the media content "
        "from these websites and displaying it in the chat. Also having some extra features like "
        "a command to download YouTube videos and audios."
    )
    doc: LazyProxy = _(
        "Automatic media download is available for the following websites:\n"
        "- X (Twitter)\n"
        "- TikTok\n\n"
        "<b>Commands:</b>\n"
        "- /ytdl &lt;youtubelink&gt;: Download the YouTube video or audio from the given link."
    )
