# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2022 Victor Cebarros <https://github.com/victorcebarros>

from hydrogram.types import Message


def get_command_name(message: Message) -> str:
    """
    Get the command name from a Message.

    This function returns the command name without the slash.

    Parameters
    ----------
    message : hydrogram.types.Message
        The Pyrogram Message object.

    Returns
    -------
    str
        The stripped command name.

    Examples
    --------
    >>> # id=0 is required to create the message type
    >>> m = Message(text="/command arg1 arg2 ... argN", id=0)
    >>> c = get_command_name(m)
    >>> c
    "command"
    """
    if message.text is None:
        return ""

    if not message.text.startswith("/"):
        return ""

    pos: int = message.text.find(" ")
    if pos == -1:
        pos = len(message.text)

    return message.text[1:pos]


def get_command_arg(message: Message) -> str:
    """
    Get the command argument from message.

    This function returns the command argument without the command name.

    Parameters
    ----------
    message : hydrogram.types.Message
        Pyrogram's Message.

    Returns
    -------
    str
        Arguments passed to the command.

    Examples
    --------
    >>> # id=0 is required to create the message type
    >>> m = Message(text="/command arg1 arg2 ... argN", id=0)
    >>> c = get_command_name(m)
    >>> c
    "arg1 arg2 ... argN"
    """
    if message is None or message.text is None:
        return ""

    pos: int = message.text.find(" ")

    if pos == -1:
        return ""

    return message.text[pos + 1 :]
