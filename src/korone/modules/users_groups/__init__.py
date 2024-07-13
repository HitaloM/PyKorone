# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from babel.support import LazyProxy

from korone.utils.i18n import lazy_gettext as _


class ModuleInfo:
    name: LazyProxy = _("Users & Groups")
    summary: LazyProxy = _(
        "This module allows retrieval of public information about users and groups, including "
        "usernames, IDs, and first names for users, and names, IDs, and usernames for groups. "
        "\n\nAll information is fetched from the Telegram API. No private information is "
        "exposed."
    )
    doc: LazyProxy = _(
        "<b>Commands:</b>\n"
        "- /user &lt;username/id&gt;: Fetches information about a user.\n"
        "- /group &lt;username/id&gt;: Fetches information about a group."
    )
