# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import inspect
from abc import ABC, abstractmethod
from asyncio import Future
from collections.abc import Coroutine
from functools import partial
from typing import Any

from hydrogram import Client
from hydrogram.filters import Filter
from hydrogram.types import Update
from magic_filter import MagicFilter


class KoroneFilter(Filter, ABC):
    """
    Base class for all filters.

    A base class for creating custom filters in the context of the Hydrogram library.
    This class should be subclassed and the __call__ method overridden to define custom
    filter logic. The custom filter can then be used to filter updates based on any criteria.

    Examples
    --------
    >>> class MyFilter(KoroneFilter):
    ...     async def __call__(self, client: Client, message: Message) -> bool:
    ...         return message.text == "Hello, world!"
    """

    @abstractmethod
    async def __call__(self, client: Client, update: Update) -> bool:
        """
        Override this method to define custom filter logic.

        This coroutine should return True if the update should be processed, False otherwise.

        Parameters
        ----------
        client : Client
            The client instance that received the update.
        update : Update
            The update to be filtered.

        Returns
        -------
        bool
            True if the update should be processed, False otherwise.
        """
        ...

    def __invert__(self) -> "InvertFilter":
        """
        Invert the filter using the NOT operator.

        Inverts the filter using the NOT operator and returns a new filter.
        The resulting filter passes only if the original filter does not pass.

        Returns
        -------
        InvertFilter
            A new filter that inverts the original filter.
        """
        return InvertFilter(self)

    def __and__(self, other) -> "AndFilter":
        """
        Combine this filter with another filter using the AND operator.

        Combines this filter with another one using logical AND.
        The resulting filter passes only if both the original and the other filter pass.

        Parameters
        ----------
        other : KoroneFilter
            The other filter to combine with this one.

        Returns
        -------
        AndFilter
            A new filter that combines this filter with the other filter using logical AND.
        """
        return AndFilter(self, other)

    def __or__(self, other) -> "OrFilter":
        """
        Combine this filter with another filter using the OR operator.

        Combines this filter with another one using logical OR and returns a new filter.
        The resulting filter passes if either the original or the other filter pass.

        Parameters
        ----------
        other : KoroneFilter
            The other filter to combine with this one.

        Returns
        -------
        OrFilter
            A new filter that combines this filter with the other filter using logical OR.
        """
        return OrFilter(self, other)


def resolve_filter(
    filter: KoroneFilter, client: Client, update: Update
) -> Future[Any] | Coroutine[Any, Any, bool] | Future[Coroutine[Any, Any, bool]]:
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
    Future[Any] | Coroutine[Any, Any, bool] | Future[Coroutine[Any, Any, bool]]
        The resolved filter value.
    """
    if inspect.iscoroutinefunction(filter.__call__):
        return filter(client, update)

    if isinstance(filter, MagicFilter):
        return client.loop.run_in_executor(client.executor, filter.resolve, update)

    return client.loop.run_in_executor(client.executor, partial(filter, client, update))


class InvertFilter(KoroneFilter):
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

    def __init__(self, base: KoroneFilter):
        self.base: KoroneFilter = base

    async def __call__(
        self, client: Client, update: Update
    ) -> Any | bool | Coroutine[Any, Any, bool]:
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
        Any | bool | Coroutine[Any, Any, bool]
            True if the update does not pass the base filter, False otherwise.
        """
        x = await resolve_filter(self.base, client, update)
        return not x


class AndFilter(KoroneFilter):
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
        self.base: KoroneFilter = base
        self.other: KoroneFilter = other

    async def __call__(
        self, client: Client, update: Update
    ) -> Any | bool | Coroutine[Any, Any, bool]:
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
        Any | bool | Coroutine[Any, Any, bool]
            True if the update passes both filters, False otherwise.
        """
        x = await resolve_filter(self.base, client, update)

        # short circuit
        if not x:
            return False

        y = await resolve_filter(self.other, client, update)
        return x and y


class OrFilter(KoroneFilter):
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
        self.base: KoroneFilter = base
        self.other: KoroneFilter = other

    async def __call__(
        self, client: Client, update: Update
    ) -> Any | bool | Coroutine[Any, Any, bool]:
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
        Any | bool | Coroutine[Any, Any, bool]
            True if the update passes either filter, False otherwise.
        """
        x = await resolve_filter(self.base, client, update)

        # short circuit
        if x:
            return True

        y = await resolve_filter(self.other, client, update)
        return x or y
