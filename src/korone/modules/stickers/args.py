from dataclasses import dataclass
from typing import override

from korone.args import ArgumentDescription, ArgumentExamples, ArgumentValueError, TextArg, TransformArg
from korone.modules.stickers.utils.pack import normalize_pack_title
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_


@dataclass(frozen=True, slots=True)
class StickerStealPackArguments:
    pack_name: str


@dataclass(frozen=True, slots=True)
class StickerStealOptions:
    pack_title: str | None = None
    emoji: str | None = None


class StickerStealOptionsArg(TransformArg[str, StickerStealOptions]):
    def __init__(self, description: ArgumentDescription | None = None) -> None:
        super().__init__(TextArg(description))

    @override
    def needed_type(self) -> tuple[ArgumentDescription, ArgumentDescription]:
        return l_("Sticker pack name and optional emoji"), l_("Sticker pack names and optional emojis")

    @property
    @override
    def examples(self) -> ArgumentExamples:
        return {"MyPack": None, "MyPack 😄": None}

    @override
    async def transform(self, value: str) -> StickerStealOptions:
        parts = value.split()
        last_part = parts[-1]
        if len(last_part[-1].encode()) == 1:
            return StickerStealOptions(pack_title=normalize_pack_title(" ".join(parts)))

        pack_title = normalize_pack_title(" ".join(parts[:-1])) if len(parts) > 1 else None
        return StickerStealOptions(pack_title=pack_title, emoji=last_part)


class StickerPackTitleArg(TransformArg[str, str]):
    def __init__(self, description: ArgumentDescription | None = None) -> None:
        super().__init__(TextArg(description))

    @override
    def needed_type(self) -> tuple[ArgumentDescription, ArgumentDescription]:
        return l_("Sticker pack name"), l_("Sticker pack names")

    @property
    @override
    def examples(self) -> ArgumentExamples:
        return {"My Pack": None}

    @override
    async def transform(self, value: str) -> str:
        return normalize_pack_title(value)


@dataclass(frozen=True, slots=True)
class StickerPackTarget:
    raw: str
    index: int | None = None
    normalized_name: str | None = None


class StickerPackTargetArg(TransformArg[str, StickerPackTarget]):
    def __init__(self, description: ArgumentDescription | None = None) -> None:
        super().__init__(TextArg(description))

    @override
    def needed_type(self) -> tuple[ArgumentDescription, ArgumentDescription]:
        return l_("Sticker pack index or name"), l_("Sticker pack indexes or names")

    @property
    @override
    def examples(self) -> ArgumentExamples:
        return {"1": l_("Pack index"), "My Pack": l_("Pack name")}

    @override
    async def transform(self, value: str) -> StickerPackTarget:
        if not value.isdigit():
            return StickerPackTarget(raw=value, normalized_name=value.casefold())

        index = int(value)
        if index < 1:
            raise ArgumentValueError(_("Sticker pack indexes start at 1."))
        return StickerPackTarget(raw=value, index=index - 1)
