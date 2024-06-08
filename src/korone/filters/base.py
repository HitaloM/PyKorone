# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from abc import ABC, abstractmethod
from collections.abc import Generator
from typing import TYPE_CHECKING

from hydrogram import Client
from hydrogram.filters import Filter
from hydrogram.types import Update

if TYPE_CHECKING:
    from korone.filters.logic import AndFilter, InvertFilter, OrFilter


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
        from korone.filters.logic import invert_f  # noqa: PLC0415

        return invert_f(self)

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
        from korone.filters.logic import and_f  # noqa: PLC0415

        return and_f(self, other)

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
        from korone.filters.logic import or_f  # noqa: PLC0415

        return or_f(self, other)

    def __await__(self) -> Generator:
        """
        Allow the filter to be used in an await expression.

        This method allows the filter to be used in an await expression.
        It is needed because the :class:`hydrogram.filters.AndFilter` tries to call the filter
        object as a coroutine.

        Returns
        -------
        Awaitable[bool]
            An awaitable object that resolves to True if the user is an administrator,
            False otherwise.
        """
        return self.__call__().__await__()  # type: ignore
