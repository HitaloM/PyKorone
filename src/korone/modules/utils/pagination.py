# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

import math
import typing
from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass
from typing import Any

from hairydogm.keyboard import InlineKeyboardBuilder
from hydrogram.types import InlineKeyboardButton

T = typing.TypeVar("T")


def default_page_callback(x: int) -> str:
    return str(x)


def default_item_callback(i: Any, pg: int) -> str:
    return f"[{pg}] {i}"


def chunk_list(lst: Sequence[T], size: int) -> Iterator[typing.Sequence[T]]:
    for i in range(0, len(lst), size):
        yield lst[i : i + size]


@dataclass
class Pagination:
    objects: list[Any]
    page_data: Callable[[int], str] = default_page_callback
    item_data: Callable[[Any, int], str] = default_item_callback
    item_title: Callable[[Any, int], str] = default_item_callback

    def create(self, page: int, lines: int = 5, columns: int = 1) -> InlineKeyboardBuilder:
        quant_per_page = lines * columns
        page = max(1, page)
        offset = (page - 1) * quant_per_page
        stop = offset + quant_per_page
        cutted = self.objects[offset:stop]

        total = len(self.objects)
        pages_range = list(range(1, math.ceil(total / quant_per_page) + 1))
        last_page = len(pages_range)

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
                ("« 1" if last_page - 4 > 1 else 1, self.page_data(1)),
                (
                    f"‹ {last_page - 3}" if last_page - 4 > 1 else last_page - 3,
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

        buttons = [(self.item_title(item, page), self.item_data(item, page)) for item in cutted]
        kb_lines = chunk_list(buttons, columns)

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
