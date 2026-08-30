import html
from typing import TYPE_CHECKING, Final

from aiogram.utils.formatting import ExpandableBlockQuote, TextLink
from aiogram.utils.keyboard import InlineKeyboardBuilder

from korone.ui import Bold, Code, Italic, Text, template
from korone.ui.rendering import plain_text
from korone.utils.i18n import gettext as _

if TYPE_CHECKING:
    from collections.abc import Callable

    from aiogram.types import InlineKeyboardMarkup

    from .models import MediaPost, ProviderInfo

CAPTION_LIMIT: Final = 1024


def _resolve_author_name(author_name: object, provider: ProviderInfo) -> str:
    return author_name if isinstance(author_name, str) and author_name else provider.name


def _resolve_author_handle(author_handle: object, provider: ProviderInfo) -> str:
    return author_handle if isinstance(author_handle, str) and author_handle else provider.name.casefold()


def _caption_title(author_name: str, author_handle: str, provider: ProviderInfo) -> Text:
    normalized_handle = author_handle.lstrip("@")
    prefix = provider.author_handle_prefix
    handle = f"{prefix}{normalized_handle}" if normalized_handle else normalized_handle
    if not provider.show_author_name:
        return Text(Code(handle), ":")
    return Text(Bold(author_name), " (", Code(handle), "):")


def _open_in_website_text(website: str) -> str:
    return plain_text(template(_("Open in {website}"), website=website))


def _caption_link(post: MediaPost, *, include_link: bool) -> Text | None:
    return TextLink(_open_in_website_text(post.website), url=post.url) if include_link else None


def _render_caption_blocks(blocks: list[Text]) -> Text:
    rendered_blocks: list[Text | str] = []
    for block in blocks:
        if rendered_blocks:
            rendered_blocks.append("\n\n")
        rendered_blocks.append(block)

    return Text(*rendered_blocks, sep="")


def _render_caption(title: Text, link: Text | None, text: str | None = None) -> Text:
    blocks: list[Text] = [title]
    if text:
        blocks.append(Italic(text))
    if link:
        blocks.append(link)

    return _render_caption_blocks(blocks)


def _truncate_segment(raw_text: str, render: Callable[[str], Text]) -> str:
    if not raw_text:
        return ""

    ellipsis = " [...]"
    low = 0
    high = len(raw_text)
    best = ""

    while low <= high:
        mid = (low + high) // 2
        truncated = raw_text[:mid].rstrip()
        text = f"{truncated}{ellipsis}" if truncated else ""
        candidate = render(text)

        if len(plain_text(candidate)) <= CAPTION_LIMIT:
            best = text
            low = mid + 1
        else:
            high = mid - 1

    return best


def _build_standard_caption(post: MediaPost, provider: ProviderInfo, *, include_link: bool) -> Text:
    title = _caption_title(
        _resolve_author_name(post.author_name, provider), _resolve_author_handle(post.author_handle, provider), provider
    )
    link = _caption_link(post, include_link=include_link)

    if not post.text:
        return _render_caption(title, link)

    candidate = _render_caption(title, link, post.text)
    if len(plain_text(candidate)) <= CAPTION_LIMIT:
        return candidate

    trimmed_text = _truncate_segment(post.text, lambda text: _render_caption(title, link, text or None))
    if not trimmed_text:
        return _render_caption(title, link)

    return _render_caption(title, link, trimmed_text)


def _normalize_quote_text(text: str) -> str:
    return html.unescape(text)


def _build_quote_block(post: MediaPost, quote_text: str) -> Text | None:
    if not (quote_text or post.quote_author_name or post.quote_author_handle):
        return None

    quote_header_parts: list[str] = []
    if post.quote_author_name:
        quote_header_parts.append(_normalize_quote_text(post.quote_author_name))

    if post.quote_author_handle:
        handle = post.quote_author_handle.lstrip("@")
        if handle:
            quote_header_parts.append(f"({_normalize_quote_text(handle)})")

    quote_lines: list[str] = []
    if quote_header_parts:
        quote_lines.append(" ".join(quote_header_parts))
    if quote_text:
        quote_lines.append(_normalize_quote_text(quote_text))

    if not quote_lines:
        return None

    return ExpandableBlockQuote("\n".join(quote_lines))


def _render_quote_caption(
    post: MediaPost, provider: ProviderInfo, *, include_link: bool, text: str, quote_text: str
) -> Text:
    title = _caption_title(
        _resolve_author_name(post.author_name, provider), _resolve_author_handle(post.author_handle, provider), provider
    )

    blocks: list[Text] = [title]
    if text:
        blocks.append(Italic(_normalize_quote_text(text)))

    if quote_block := _build_quote_block(post, quote_text):
        blocks.append(quote_block)

    link = _caption_link(post, include_link=include_link)
    if link:
        blocks.append(link)

    return _render_caption_blocks(blocks)


def _build_quote_caption(post: MediaPost, provider: ProviderInfo, *, include_link: bool) -> Text:
    text = post.text.strip()
    quote_text = (post.quote_text or "").strip()

    def render(current_text: str, current_quote_text: str) -> Text:
        return _render_quote_caption(
            post, provider, include_link=include_link, text=current_text, quote_text=current_quote_text
        )

    candidate = render(text, quote_text)
    if len(plain_text(candidate)) <= CAPTION_LIMIT:
        return candidate

    if quote_text:
        quote_text = _truncate_segment(quote_text, lambda value: render(text, value))
        candidate = render(text, quote_text)
        if len(plain_text(candidate)) <= CAPTION_LIMIT:
            return candidate

    if text:
        text = _truncate_segment(text, lambda value: render(value, quote_text))
        candidate = render(text, quote_text)
        if len(plain_text(candidate)) <= CAPTION_LIMIT:
            return candidate

    candidate = render(text, "")
    if len(plain_text(candidate)) <= CAPTION_LIMIT:
        return candidate

    if text:
        text = _truncate_segment(text, lambda value: render(value, ""))
        candidate = render(text, "")
        if len(plain_text(candidate)) <= CAPTION_LIMIT:
            return candidate

    return _build_standard_caption(post, provider, include_link=include_link)


def build_caption(post: MediaPost, provider: ProviderInfo, *, include_link: bool) -> Text:
    if post.quote_text or post.quote_author_name or post.quote_author_handle:
        return _build_quote_caption(post, provider, include_link=include_link)

    return _build_standard_caption(post, provider, include_link=include_link)


def build_keyboard(post: MediaPost) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=_open_in_website_text(post.website), url=post.url)
    return builder.as_markup()
