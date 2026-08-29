import re
from dataclasses import dataclass
from typing import override

from korone.args import ArgumentDescription, ArgumentExamples, ArgumentValueError, TextArg, TransformArg, WordArg
from korone.modules.lastfm.utils.collage import MAX_SIZE, MIN_SIZE
from korone.modules.lastfm.utils.periods import LastFMPeriod, parse_period_token
from korone.ui import Code, template
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_

USERNAME_RE = re.compile(r"^[A-Za-z0-9_.-]{1,64}$")
COLLAGE_CLEAN_TOKENS = frozenset({"clean", "notext", "nonames"})


class LastFMUsernameArg(TransformArg[str, str]):
    def __init__(self, description: ArgumentDescription | None = None) -> None:
        super().__init__(WordArg(description))

    @override
    def needed_type(self) -> tuple[ArgumentDescription, ArgumentDescription]:
        return l_("Last.fm username"), l_("Last.fm usernames")

    @property
    @override
    def examples(self) -> ArgumentExamples:
        return {"username": None, "@username": None}

    @override
    async def transform(self, value: str) -> str:
        username = value.removeprefix("@")
        if not USERNAME_RE.fullmatch(username):
            raise ArgumentValueError(_("Invalid Last.fm username format."))
        return username


class LastFMPeriodArg(TransformArg[str, LastFMPeriod]):
    def __init__(self, description: ArgumentDescription | None = None) -> None:
        super().__init__(WordArg(description))

    @override
    def needed_type(self) -> tuple[ArgumentDescription, ArgumentDescription]:
        return l_("Last.fm period"), l_("Last.fm periods")

    @property
    @override
    def examples(self) -> ArgumentExamples:
        return {"all": l_("All-time"), "1y": l_("One year"), "7d": l_("One week")}

    @override
    async def transform(self, value: str) -> LastFMPeriod:
        period = parse_period_token(value)
        if period is None:
            raise ArgumentValueError(template(_("Invalid Last.fm period: {period}."), period=Code(value)))
        return period


@dataclass(frozen=True, slots=True)
class LastFMCollageOptions:
    size: int = 3
    period: LastFMPeriod = LastFMPeriod.OVERALL
    include_text: bool = True


def _parse_collage_size(token: str) -> int | None:
    dimensions = token.split("x")
    if len(dimensions) == 1 or (len(dimensions) == 2 and dimensions[0] == dimensions[1]):
        fragment = dimensions[0]
    else:
        return None

    if not fragment.isdigit():
        return None

    size = int(fragment)
    if MIN_SIZE <= size <= MAX_SIZE:
        return size
    return None


class LastFMCollageOptionsArg(TransformArg[str, LastFMCollageOptions]):
    def __init__(self, description: ArgumentDescription | None = None) -> None:
        super().__init__(TextArg(description))

    @override
    def needed_type(self) -> tuple[ArgumentDescription, ArgumentDescription]:
        return l_("Last.fm collage options"), l_("Last.fm collage options")

    @property
    @override
    def examples(self) -> ArgumentExamples:
        return {
            "2x2": l_("Collage size"),
            "3x3 clean": l_("Collage without text"),
            "4x4 1y": l_("Collage size and period"),
        }

    @override
    async def transform(self, value: str) -> LastFMCollageOptions:
        options = LastFMCollageOptions()
        for token in value.casefold().split():
            if token in COLLAGE_CLEAN_TOKENS:
                options = LastFMCollageOptions(size=options.size, period=options.period, include_text=False)
                continue

            if size := _parse_collage_size(token):
                options = LastFMCollageOptions(size=size, period=options.period, include_text=options.include_text)
                continue

            if period := parse_period_token(token):
                options = LastFMCollageOptions(size=options.size, period=period, include_text=options.include_text)
                continue

            raise ArgumentValueError(template(_("Unknown collage option: {option}."), option=Code(token)))

        return options
