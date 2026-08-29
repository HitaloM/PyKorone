from typing import TYPE_CHECKING, Any

from .compiler import compile_ui

if TYPE_CHECKING:
    from aiogram.utils.formatting import Text

    from .expression import MessageContent


def as_text(content: MessageContent) -> Text:
    return compile_ui(content)


def plain_text(content: MessageContent) -> str:
    if isinstance(content, str):
        return content
    return as_text(content).render()[0]


def _with_kwargs(payload: dict[str, Any], kwargs: dict[str, object]) -> dict[str, Any]:
    conflicts = payload.keys() & kwargs.keys()
    if conflicts:
        names = ", ".join(sorted(conflicts))
        msg = f"Rendered payload keys cannot be overridden: {names}"
        raise TypeError(msg)
    return {**payload, **kwargs}


def text_kwargs(content: MessageContent, /, **kwargs: object) -> dict[str, Any]:
    return _with_kwargs(as_text(content).as_kwargs(), kwargs)


def caption_kwargs(content: MessageContent, /, **kwargs: object) -> dict[str, Any]:
    return _with_kwargs(as_text(content).as_caption_kwargs(), kwargs)


def message_text_kwargs(content: MessageContent, /, **kwargs: object) -> dict[str, Any]:
    return _with_kwargs(as_text(content).as_kwargs(text_key="message_text"), kwargs)
