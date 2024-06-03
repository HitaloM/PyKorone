# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from korone.modules.lastfm.utils.api import TimePeriod
from korone.utils.i18n import gettext as _


def period_to_str(period: TimePeriod) -> str:
    if period == TimePeriod.OneWeek:
        return _("1 week")
    if period == TimePeriod.OneMonth:
        return _("1 month")
    if period == TimePeriod.ThreeMonths:
        return _("3 months")
    if period == TimePeriod.SixMonths:
        return _("6 months")
    if period == TimePeriod.OneYear:
        return _("1 year")
    return _("All time")
