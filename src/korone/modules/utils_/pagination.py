from __future__ import annotations

import math
from itertools import islice
from typing import TYPE_CHECKING, Any

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Sequence


class Pagination:
    __slots__ = ("item_data", "item_title", "objects", "page_data")

    def __init__(
        self,
        objects: list[Any],
        page_data: Callable[[int], str],
        item_data: Callable[[Any, int], str],
        item_title: Callable[[Any, int], str],
    ) -> None:
        self.objects = objects
        self.page_data = page_data
        self.item_data = item_data
        self.item_title = item_title

    @staticmethod
    def chunk_list(lst: Sequence[Any], size: int) -> Iterator[Sequence[Any]]:
        it = iter(lst)
        for first in it:
            yield [first, *list(islice(it, size - 1))]

    def create(self, page: int, lines: int = 5, columns: int = 1) -> InlineKeyboardMarkup:
        items_per_page = lines * columns
        page = max(1, page)
        offset = (page - 1) * items_per_page
        total_items = len(self.objects)
        last_page = math.ceil(total_items / items_per_page)

        current_page_items = self.objects[offset : offset + items_per_page]

        buttons = [(self.item_title(item, page), self.item_data(item, page)) for item in current_page_items]
        kb_lines = list(self.chunk_list(buttons, columns))

        if last_page > 1:
            pages_range = range(1, last_page + 1)
            nav_buttons = self._generate_navigation_buttons(page, last_page, pages_range)
            kb_lines.append(nav_buttons)

        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=str(text), callback_data=data) for text, data in line] for line in kb_lines
            ]
        )

    @staticmethod
    def _format_page_number(n: int, current_page: int) -> str:
        return f"· {n} ·" if n == current_page else str(n)

    def _generate_navigation_buttons(self, page: int, last_page: int, pages_range: range) -> list[tuple[str, str]]:
        if last_page <= 5:
            return [(self._format_page_number(n, page), self.page_data(n)) for n in pages_range]
        if page <= 3:
            return self._generate_first_section_navigation(page, last_page, pages_range)
        if page >= last_page - 2:
            return self._generate_last_section_navigation(page, last_page, pages_range)
        return self._generate_middle_section_navigation(page, last_page)

    def _generate_first_section_navigation(
        self, page: int, last_page: int, pages_range: range
    ) -> list[tuple[str, str]]:
        nav = [(self._format_page_number(n, page), self.page_data(n)) for n in pages_range[:3]]

        if last_page >= 4:
            nav.append(("4 ›" if last_page > 5 else "4", self.page_data(4)))

        if last_page > 4:
            nav.append((f"{last_page} »" if last_page > 5 else str(last_page), self.page_data(last_page)))

        return nav

    def _generate_last_section_navigation(self, page: int, last_page: int, pages_range: range) -> list[tuple[str, str]]:
        nav = [("« 1" if last_page > 5 else "1", self.page_data(1))]
        if last_page > 5:
            nav.append((f"‹ {last_page - 3}", self.page_data(last_page - 3)))

        nav.extend((self._format_page_number(n, page), self.page_data(n)) for n in pages_range[-3:])

        return nav

    def _generate_middle_section_navigation(self, page: int, last_page: int) -> list[tuple[str, str]]:
        return [
            ("« 1", self.page_data(1)),
            (f"‹ {page - 1}", self.page_data(page - 1)),
            (f"· {page} ·", "noop"),
            (f"{page + 1} ›", self.page_data(page + 1)),
            (f"{last_page} »", self.page_data(last_page)),
        ]
