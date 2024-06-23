# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from babel.support import LazyProxy

from korone.utils.i18n import lazy_gettext as _


class ModuleInfo:
    name: LazyProxy = _("Web Tools")
    summary: LazyProxy = _(
        "This module provides tools to interact with the web, such as whois queries."
    )
    doc: LazyProxy = _(
        "<b>Commands:</b>\n"
        "- /whois &lt;domain&gt;: Fetches whois information for a domain.\n"
        "- /ip &lt;ip/domain&gt;: Fetches information about an IP address or domain."
    )
