from typing import Any

from aiogram.utils.formatting import Text

from korone.utils.i18n import LazyProxy


class UIExpression:
    __slots__ = ()

    def compile(self) -> Text:
        from .compiler import compile_ui  # ruff: ignore[import-outside-top-level]

        return compile_ui(self)

    def as_kwargs(self) -> dict[str, Any]:
        return self.compile().as_kwargs()

    def as_caption_kwargs(self) -> dict[str, Any]:
        return self.compile().as_caption_kwargs()


type UI = UIExpression | Text
type Renderable = UI | LazyProxy | str | int | float
type MessageContent = UI | str
