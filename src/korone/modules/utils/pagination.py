# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

import math
import typing
from collections.abc import Callable, Iterator, Sequence
from typing import Any

from hairydogm.keyboard import InlineKeyboardBuilder
from hydrogram.types import InlineKeyboardButton

T = typing.TypeVar("T")


def default_page_callback(x: int) -> str:
    """
    Convert an integer page number to a string representation.

    This function takes an integer page number as input and converts it to
    a string representation. The string representation is then returned as the output.

    Parameters
    ----------
    x : int
        The page number to convert.

    Returns
    -------
    str
        The string representation of the page number.
    """
    return str(x)


def default_item_callback(i: Any, pg: int) -> str:
    """
    Format the item with the page number.

    This function takes an item and a page number as input and returns a formatted string
    that includes the page number and the item. The format of the returned string is
    '[page_number] item'.

    Parameters
    ----------
    i : typing.Any
        The item to be formatted.
    pg : int
        The page number.

    Returns
    -------
    str
        The formatted item with the page number.
    """
    return f"[{pg}] {i}"


def chunk_list(lst: Sequence[T], size: int) -> Iterator[typing.Sequence[T]]:
    """
    Split a list into smaller chunks of a specified size.

    This function takes a list and divides it into smaller chunks of the specified size.
    Each chunk is returned as an iterator, allowing for efficient memory usage when working
    with large lists.

    Parameters
    ----------
    lst : typing.Sequence[T]
        The list to be chunked.
    size : int
        The size of each chunk.

    Yields
    ------
    typing.Iterator[typing.Sequence[T]]
        An iterator that yields chunks of the original list.

    Examples
    --------
    >>> lst = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    >>> for chunk in chunk_list(lst, 3):
    ...     print(chunk)
    [1, 2, 3]
    [4, 5, 6]
    [7, 8, 9]
    [10]
    """
    for i in range(0, len(lst), size):
        yield lst[i : i + size]


class Pagination:
    """
    A class that represents a pagination utility.

    This class provides functionality for paginating a list of objects and retrieving data for
    specific pages and items on those pages.

    Parameters
    ----------
    objects : list[Any]
        The list of objects to be paginated.
    page_data : typing.Callable[[int], str], optional
        A function that returns the data for a specific page. Defaults to
        `default_page_callback`.
    item_data : typing.Callable[[Any, int], str], optional
        A function that returns the data for a specific item on a page. Defaults to
        `default_item_callback`.
    item_title : typing.Callable[[Any, int], str], optional
        A function that returns the title for a specific item on a page. Defaults to
        `default_item_callback`.
    """

    def __init__(
        self,
        objects: list[Any],
        page_data: Callable[[int], str] = default_page_callback,
        item_data: Callable[[Any, int], str] = default_item_callback,
        item_title: Callable[[Any, int], str] = default_item_callback,
    ):
        self.objects = objects
        self.page_data = page_data
        self.item_data = item_data
        self.item_title = item_title

    def create(self, page: int, lines: int = 5, columns: int = 1) -> InlineKeyboardBuilder:
        """
        Create a pagination with the specified parameters.

        This method generates a pagination for a given list of objects, allowing navigation
        between pages. The pagination is created based on the current page number, number of
        lines per page, and number of columns per page.

        Parameters
        ----------
        page : int
            The current page number.
        lines : int, optional
            The number of lines per page. Defaults to 5.
        columns : int, optional
            The number of columns per page. Defaults to 1.

        Returns
        -------
        hairydogm.keyboard.InlineKeyboardBuilder
            The created pagination.
        """
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
