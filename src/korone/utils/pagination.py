# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

from __future__ import annotations

import math
from itertools import islice
from typing import TYPE_CHECKING, Any

from hydrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Sequence


class Pagination:
    """A utility class to create paginated inline keyboards.

    This class helps with creating paginated menus in Telegram inline keyboards
    by handling the pagination logic and generating appropriate navigation buttons.

    Attributes:
        objects: List of objects to paginate.
        page_data: Function that generates callback data for page navigation.
        item_data: Function that generates callback data for individual items.
        item_title: Function that generates display text for individual items.
    """

    __slots__ = ("item_data", "item_title", "objects", "page_data")

    def __init__(
        self,
        objects: list[Any],
        page_data: Callable[[int], str],
        item_data: Callable[[Any, int], str],
        item_title: Callable[[Any, int], str],
    ) -> None:
        """Initialize a pagination object.

        Args:
            objects: List of items to be paginated.
            page_data: Function that returns callback data for page navigation buttons.
            item_data: Function that returns callback data for each item button.
            item_title: Function that returns display text for each item button.
        """
        self.objects = objects
        self.page_data = page_data
        self.item_data = item_data
        self.item_title = item_title

    @staticmethod
    def chunk_list(lst: Sequence[Any], size: int) -> Iterator[Sequence[Any]]:
        """Split a sequence into chunks of specified size.

        Args:
            lst: The sequence to be chunked.
            size: Maximum size of each chunk.

        Yields:
            Sequence[Any]: Subsequences containing up to ``size`` items.
        """
        it = iter(lst)
        for first in it:
            yield [first, *list(islice(it, size - 1))]

    def create(self, page: int, lines: int = 5, columns: int = 1) -> InlineKeyboardMarkup:
        """Create a paginated inline keyboard.

        Args:
            page: Current page number (1-indexed).
            lines: Number of lines per page.
            columns: Number of columns per page.

        Returns:
            An InlineKeyboardMarkup object with paginated buttons.
        """
        items_per_page = lines * columns
        page = max(1, page)
        offset = (page - 1) * items_per_page
        total_items = len(self.objects)
        last_page = math.ceil(total_items / items_per_page)

        current_page_items = self.objects[offset : offset + items_per_page]

        buttons = [
            (self.item_title(item, page), self.item_data(item, page))
            for item in current_page_items
        ]
        kb_lines = list(self.chunk_list(buttons, columns))

        if last_page > 1:
            pages_range = range(1, last_page + 1)
            nav_buttons = self._generate_navigation_buttons(page, last_page, pages_range)
            kb_lines.append(nav_buttons)

        return InlineKeyboardMarkup([
            [InlineKeyboardButton(text=str(text), callback_data=data) for text, data in line]
            for line in kb_lines
        ])

    @staticmethod
    def _format_page_number(n: int, current_page: int) -> str:
        """Format a page number for display in the navigation buttons.

        Args:
            n: The page number to format.
            current_page: The current page number.

        Returns:
            Formatted page number string with highlighting for current page.
        """
        return f"· {n} ·" if n == current_page else str(n)

    def _generate_navigation_buttons(
        self, page: int, last_page: int, pages_range: range
    ) -> list[tuple[str, str]]:
        """Generate navigation buttons based on current page and total pages.

        Args:
            page: Current page number.
            last_page: Last page number.
            pages_range: Range of all page numbers.

        Returns:
            List of (button_text, callback_data) tuples for navigation buttons.
        """
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
        """Generate navigation buttons for when viewing first pages.

        Args:
            page: Current page number.
            last_page: Last page number.
            pages_range: Range of all page numbers.

        Returns:
            List of (button_text, callback_data) tuples for navigation buttons.
        """
        nav = [(self._format_page_number(n, page), self.page_data(n)) for n in pages_range[:3]]

        if last_page >= 4:
            nav.append(("4 ›" if last_page > 5 else "4", self.page_data(4)))

        if last_page > 4:
            nav.append((
                f"{last_page} »" if last_page > 5 else str(last_page),
                self.page_data(last_page),
            ))

        return nav

    def _generate_last_section_navigation(
        self, page: int, last_page: int, pages_range: range
    ) -> list[tuple[str, str]]:
        """Generate navigation buttons for when viewing last pages.

        Args:
            page: Current page number.
            last_page: Last page number.
            pages_range: Range of all page numbers.

        Returns:
            List of (button_text, callback_data) tuples for navigation buttons.
        """
        nav = [("« 1" if last_page > 5 else "1", self.page_data(1))]
        if last_page > 5:
            nav.append((f"‹ {last_page - 3}", self.page_data(last_page - 3)))

        nav.extend(
            (self._format_page_number(n, page), self.page_data(n)) for n in pages_range[-3:]
        )

        return nav

    def _generate_middle_section_navigation(
        self, page: int, last_page: int
    ) -> list[tuple[str, str]]:
        """Generate navigation buttons for when viewing middle pages.

        Args:
            page: Current page number.
            last_page: Last page number.

        Returns:
            List of (button_text, callback_data) tuples for navigation buttons.
        """
        return [
            ("« 1", self.page_data(1)),
            (f"‹ {page - 1}", self.page_data(page - 1)),
            (f"· {page} ·", "noop"),
            (f"{page + 1} ›", self.page_data(page + 1)),
            (f"{last_page} »", self.page_data(last_page)),
        ]
