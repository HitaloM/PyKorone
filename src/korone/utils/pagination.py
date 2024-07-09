# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import math
import typing
from collections.abc import Callable, Iterator, Sequence
from itertools import islice
from typing import Any

from hairydogm.keyboard import InlineKeyboardBuilder
from hydrogram.types import InlineKeyboardButton


class Pagination:
    __slots__ = ("item_data", "item_title", "objects", "page_data")

    def __init__(
        self,
        objects: list[Any],
        page_data: Callable[[int], str],
        item_data: Callable[[Any, int], str],
        item_title: Callable[[Any, int], str],
    ):
        self.objects = objects
        self.page_data = page_data
        self.item_data = item_data
        self.item_title = item_title

    @staticmethod
    def chunk_list(lst: Sequence[Any], size: int) -> Iterator[typing.Sequence[Any]]:
        it = iter(lst)
        while chunk := list(islice(it, size)):
            yield chunk

    def create(self, page: int, lines: int = 5, columns: int = 1) -> InlineKeyboardBuilder:
        quant_per_page = lines * columns
        page = max(1, page)
        offset = (page - 1) * quant_per_page
        stop = offset + quant_per_page
        cutted = self.objects[offset:stop]

        total = len(self.objects)
        pages_range = list(range(1, math.ceil(total / quant_per_page) + 1))
        last_page = len(pages_range)
        nav = self._generate_navigation_buttons(page, last_page, pages_range)

        buttons = [(self.item_title(item, page), self.item_data(item, page)) for item in cutted]
        kb_lines = self.chunk_list(buttons, columns)

        if last_page > 1:
            kb_lines = list(kb_lines)
            kb_lines.append(nav)

        keyboard_markup = InlineKeyboardBuilder()
        for line in kb_lines:
            keyboard_markup.row(
                *(
                    InlineKeyboardButton(text=str(button[0]), callback_data=button[1])
                    for button in line
                )
            )

        return keyboard_markup

    def _generate_navigation_buttons(
        self, page: int, last_page: int, pages_range: list[int]
    ) -> list[tuple[str, str]]:
        nav = []

        if page <= 3:
            for n in [1, 2, 3]:
                if n in pages_range:
                    text = f"· {n} ·" if n == page else n
                    nav.append((text, self.page_data(n)))

            if last_page >= 4:
                nav.append(("4 ›" if last_page > 5 else 4, self.page_data(4)))

            if last_page > 4:
                nav.append((
                    f"{last_page} »" if last_page > 5 else last_page,
                    self.page_data(last_page),
                ))

        elif page >= last_page - 2:
            nav.extend([
                ("« 1" if last_page > 5 else 1, self.page_data(1)),
                (
                    f"‹ {last_page - 3}" if last_page > 5 else last_page - 3,
                    self.page_data(last_page - 3),
                ),
            ])

            for n in range(last_page - 2, last_page + 1):
                if n in pages_range:
                    text = f"· {n} ·" if n == page else n
                    nav.append((text, self.page_data(n)))

        else:
            nav = [
                ("« 1", self.page_data(1)),
                (f"‹ {page - 1}", self.page_data(page - 1)),
                (f"· {page} ·", "noop"),
                (f"{page + 1} ›", self.page_data(page + 1)),
                (f"{last_page} »", self.page_data(last_page)),
            ]

        return nav
