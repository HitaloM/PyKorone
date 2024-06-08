# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import inspect
from abc import ABC
from asyncio import Future
from collections.abc import Coroutine
from functools import partial
from typing import Any

from hydrogram import Client
from hydrogram.types import Update
from magic_filter import MagicFilter

from korone.filters.base import KoroneFilter


def resolve_filter(
    filter: KoroneFilter, client: Client, update: Update
) -> Future[Any] | Coroutine[Any, Any, bool]:
    """
    Resolve a filter to a boolean value.

    Resolves a filter to a boolean value by calling the filter with the given client and update.
    If the filter is a coroutine, it is awaited. If the filter is a MagicFilter, it is resolved
    using the MagicFilter.resolve method. Otherwise, the filter is called with the client and
    update and the result is returned.

    Parameters
    ----------
    filter : KoroneFilter
        The filter to resolve.
    client : Client
        The client instance that received the update.
    update : Update
        The update to filter.

    Returns
    -------
    Future[Any] | Coroutine[Any, Any, bool]
        The resolved filter value.
    """
    if inspect.iscoroutinefunction(filter.__call__):
        return filter(client, update)

    if isinstance(filter, MagicFilter):
        return client.loop.run_in_executor(client.executor, filter.resolve, update)

    return client.loop.run_in_executor(client.executor, partial(filter, client, update))


class LogicFilter(KoroneFilter, ABC):
    """
    A base class for logic filters in the PyKorone library.

    This class inherits from the `KoroneFilter` class and the `ABC` (Abstract Base Class) module.
    Logic filters are used to perform logical operations on data in PyKorone.
    """

    ...


class InvertFilter(LogicFilter):
    """
    A filter that inverts the result of another filter.

    This filter takes another filter as its base and returns the opposite result.
    If the base filter passes, the `InvertFilter` fails, and vice versa.

    Parameters
    ----------
    base : KoroneFilter
        The base filter to invert.
    """

    __slots__ = ("base",)

    def __init__(self, base: KoroneFilter) -> None:
        self.base = base

    async def __call__(self, client: Client, update: Update) -> bool:
        """
        Determine if the update does not pass the base filter.

        This method determines if the update does not pass the base filter by calling the base
        filter with the given client and update and returning the opposite result.

        Parameters
        ----------
        client : Client
            The client instance that received the update.
        update : Update
            The update to filter.

        Returns
        -------
        bool
            True if the update does not pass the base filter, False otherwise.
        """
        return not await resolve_filter(self.base, client, update)


class AndFilter(LogicFilter):
    """
    A filter that combines two filters using logical AND.

    A filter that combines two filters using logical AND. The resulting filter passes only if both
    the base and the other filter pass.

    Parameters
    ----------
    base : KoroneFilter
        The base filter.
    other : KoroneFilter
        The other filter.
    """

    __slots__ = ("base", "other")

    def __init__(self, base: KoroneFilter, other: KoroneFilter) -> None:
        self.base = base
        self.other = other

    async def __call__(self, client: Client, update: Update) -> Any | bool:
        """
        Determine if the update passes both filters.

        Combines the base and other filters using logical AND. The resulting filter passes only if
        both the base and the other filter pass.

        Parameters
        ----------
        client : Client
            The client instance that received the update.
        update : Update
            The update to filter.

        Returns
        -------
        Any | bool
            True if the update passes both filters, False otherwise.
        """
        x = await resolve_filter(self.base, client, update)

        # short circuit
        if not x:
            return False

        y = await resolve_filter(self.other, client, update)
        return x and y


class OrFilter(LogicFilter):
    """
    A filter that combines two filters using logical OR.

    A filter that combines two filters using logical OR. The resulting filter passes if either the
    base or the other filter pass.

    Parameters
    ----------
    base : KoroneFilter
        The base filter.
    other : KoroneFilter
        The other filter.
    """

    __slots__ = ("base", "other")

    def __init__(self, base: KoroneFilter, other: KoroneFilter):
        self.base = base
        self.other = other

    async def __call__(self, client: Client, update: Update) -> Any | bool:
        """
        Determine if the update passes either filter.

        Combines the base and other filters using logical OR. The resulting filter passes if either
        the base or the other filter pass.

        Parameters
        ----------
        client : Client
            The client instance that received the update.
        update : Update
            The update to filter.

        Returns
        -------
        Any | bool
            True if the update passes either filter, False otherwise.
        """
        x = await resolve_filter(self.base, client, update)

        # short circuit
        if x:
            return True

        y = await resolve_filter(self.other, client, update)
        return x or y


def invert_f(base: KoroneFilter) -> InvertFilter:
    """
    Invert a filter using the NOT operator.

    Inverts a filter using the NOT operator. The resulting filter passes only if the original
    filter does not pass.

    Parameters
    ----------
    base : KoroneFilter
        The base filter to invert.

    Returns
    -------
    InvertFilter
        A new filter that inverts the original filter.
    """
    return InvertFilter(base)


def and_f(base: KoroneFilter, other: KoroneFilter) -> AndFilter:
    """
    Combine two filters using logical AND.

    Combines two filters using logical AND. The resulting filter passes only if both the base and
    the other filter pass.

    Parameters
    ----------
    base : KoroneFilter
        The base filter.
    other : KoroneFilter
        The other filter.

    Returns
    -------
    AndFilter
        A new filter that combines the base and other filters using logical AND.
    """
    return AndFilter(base, other)


def or_f(base: KoroneFilter, other: KoroneFilter) -> OrFilter:
    """
    Combine two filters using logical OR.

    Combines two filters using logical OR. The resulting filter passes if either the base or the
    other filter pass.

    Parameters
    ----------
    base : KoroneFilter
        The base filter.
    other : KoroneFilter
        The other filter.

    Returns
    -------
    OrFilter
        A new filter that combines the base and other filters using logical OR.
    """
    return OrFilter(base, other)
