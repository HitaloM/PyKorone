# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from babel.support import LazyProxy

from korone.utils.i18n import lazy_gettext as _


class ModuleInfo:
    name: LazyProxy = _("GSM Arena")
    summary: LazyProxy = _(
        "Obtaining smartphone specifications can be a tedious task, especially when it involves "
        "navigating through multiple websites or pages.\n\n"
        "This module simplifies the process by enabling users to obtain the specifications of "
        "a particular device directly from Telegram."
    )
    doc: LazyProxy = _(
        "<b>Commands:</b>\n- /device &lt;device name&gt;: Returns the specifications of a device."
    )
