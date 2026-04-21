from __future__ import annotations

import html
from typing import TYPE_CHECKING

from aiogram.utils.formatting import ExpandableBlockQuote, Italic, Text

from korone.modules.medias.utils.platforms import TwitterProvider

from .base import BaseMediaHandler

if TYPE_CHECKING:
    from collections.abc import Callable

    from korone.modules.medias.utils.types import MediaPost


class TwitterMediaHandler(BaseMediaHandler):
    PROVIDER = TwitterProvider
    DEFAULT_AUTHOR_NAME = "Twitter"
    DEFAULT_AUTHOR_HANDLE = "twitter"

    @staticmethod
    def _normalize_text(text: str) -> str:
        return html.unescape(text)

    @classmethod
    def _build_quote_block(cls, post: MediaPost, quote_text: str) -> Text | None:
        if not (quote_text or post.quote_author_name or post.quote_author_handle):
            return None

        quote_header_parts: list[str] = []
        if post.quote_author_name:
            quote_header_parts.append(cls._normalize_text(post.quote_author_name))

        if post.quote_author_handle:
            handle = post.quote_author_handle.lstrip("@")
            if handle:
                quote_header_parts.append(f"({cls._normalize_text(handle)})")

        quote_lines: list[str] = []
        if quote_header_parts:
            quote_lines.append(" ".join(quote_header_parts))
        if quote_text:
            quote_lines.append(cls._normalize_text(quote_text))

        if not quote_lines:
            return None

        return ExpandableBlockQuote("\n".join(quote_lines))

    @classmethod
    def _render_twitter_caption(cls, post: MediaPost, *, include_link: bool, text: str, quote_text: str) -> str:
        title = cls._caption_title(
            post.author_name or cls.DEFAULT_AUTHOR_NAME, post.author_handle or cls.DEFAULT_AUTHOR_HANDLE
        )

        blocks: list[Text] = [title]
        if text:
            blocks.append(Italic(cls._normalize_text(text)))

        if quote_block := cls._build_quote_block(post, quote_text):
            blocks.append(quote_block)

        link = cls._caption_link(post, include_link=include_link)
        if link:
            blocks.append(link)

        rendered_blocks: list[Text | str] = []
        for block in blocks:
            if rendered_blocks:
                rendered_blocks.append("\n\n")
            rendered_blocks.append(block)

        return Text(*rendered_blocks, sep="").as_html()

    @classmethod
    def _truncate_segment(cls, raw_text: str, render: Callable[[str], str]) -> str:
        if not raw_text:
            return ""

        ellipsis = " [...]"
        low = 0
        high = len(raw_text)
        best = ""

        while low <= high:
            mid = (low + high) // 2
            truncated = raw_text[:mid].rstrip()
            candidate_text = f"{truncated}{ellipsis}" if truncated else ""
            candidate = render(candidate_text)

            if len(candidate) <= cls.CAPTION_LIMIT:
                best = candidate_text
                low = mid + 1
            else:
                high = mid - 1

        return best

    @classmethod
    def _build_caption(cls, post: MediaPost, *, include_link: bool) -> str:
        has_quote_data = bool(post.quote_text or post.quote_author_name or post.quote_author_handle)
        if not has_quote_data:
            return super()._build_caption(post, include_link=include_link)

        text = post.text.strip()
        quote_text = (post.quote_text or "").strip()

        def render(current_text: str, current_quote_text: str) -> str:
            return cls._render_twitter_caption(
                post, include_link=include_link, text=current_text, quote_text=current_quote_text
            )

        candidate = render(text, quote_text)
        if len(candidate) <= cls.CAPTION_LIMIT:
            return candidate

        if quote_text:
            quote_text = cls._truncate_segment(quote_text, lambda value: render(text, value))
            candidate = render(text, quote_text)
            if len(candidate) <= cls.CAPTION_LIMIT:
                return candidate

        if text:
            text = cls._truncate_segment(text, lambda value: render(value, quote_text))
            candidate = render(text, quote_text)
            if len(candidate) <= cls.CAPTION_LIMIT:
                return candidate

        candidate = render(text, "")
        if len(candidate) <= cls.CAPTION_LIMIT:
            return candidate

        if text:
            text = cls._truncate_segment(text, lambda value: render(value, ""))
            candidate = render(text, "")
            if len(candidate) <= cls.CAPTION_LIMIT:
                return candidate

        return super()._build_caption(post, include_link=include_link)
