# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

from korone.decorators.factory import Factory


class RouterError(Exception):
    """
    An exception that is raised when a unsupported event is called.

    This exception is raised when a unsupported event is called by the user.
    """


class Router:
    """
    A class that represents a decorators router.

    This class is used to create a router for the decorators, it receives the
    name of the decorator as a parameter and returns the class that will be
    used to create the decorator.

    Attributes
    ----------
    message : Factory
        A Factory instance for creating message decorators.
    callback_query : Factory
        A Factory instance for creating callback query decorators.
    """

    __slots__ = ("callback_query", "message")

    def __init__(self) -> None:
        self.message = Factory("message")
        self.callback_query = Factory("callback_query")

    def __getattr__(self, name: str):
        """
        Get the class that will be used to create the decorator.

        This method is called when an attribute is accessed that doesn't exist in the object.
        It raises a RouterError indicating that the event type is not supported by PyKorone.

        Parameters
        ----------
        name : str
            The name of the attribute that was accessed.

        Raises
        ------
        RouterError
            When a unsupported event is called.
        """
        msg = f"Event of type: '{name}' is not supported by the PyKorone."
        raise RouterError(msg)
