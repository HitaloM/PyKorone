# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

import sys
from dataclasses import dataclass
from pathlib import Path

import hydrogram
from cashews import cache
from cashews.exceptions import CacheBackendInteractionError
from hydrogram import Client
from hydrogram.enums import ParseMode
from hydrogram.raw.all import layer
from hydrogram.types import User

from korone import constants
from korone.database.impl import SQLite3Connection
from korone.modules import load_all_modules
from korone.utils.logging import log


@dataclass
class AppParameters:
    """
    Parameters for :obj:`hydrogram.Client`.

    This class represents the parameters for initializing the bot.
    """

    api_id: str
    """The Telegram API ID.

    :type: str
    """
    api_hash: str
    """The Telegram API Hash.

    :type: str
    """
    bot_token: str
    """The Telegram bot token.

    :type: str
    """
    ipv6: bool = True
    """Whether to use IPv6 to connect to Telegram servers.

    :type: bool"""
    name: str = constants.CLIENT_NAME
    """The name of the :class:`hydrogram.Client`.

    :type: str
    """
    workers: int = constants.WORKERS
    """The number of workers to be used by the :class:`hydrogram.Client`.

    :type: int
    """


class Korone(Client):
    """
    Represent Korone.

    This class represents Korone. It inherits from :obj:`hydrogram.Client`.

    Parameters
    ----------
    parameters : AppParameters
        The parameters for initializing the bot.

    Attributes
    ----------
    parameters : AppParameters
        The parameters for initializing the bot.
    me : hydrogram.types.User
        The user representing the bot.
    """

    __slots__ = ("parameters",)

    def __init__(self, parameters: AppParameters):
        self.parameters = parameters
        self.me: User

        super().__init__(
            name=self.parameters.name,
            api_id=self.parameters.api_id,
            api_hash=self.parameters.api_hash,
            bot_token=self.parameters.bot_token,
            workers=self.parameters.workers,
            ipv6=self.parameters.ipv6,
            parse_mode=ParseMode.HTML,
            workdir=Path(__file__).parent.parent.as_posix(),
            sleep_threshold=180,
        )

    async def start(self) -> None:
        """
        Start the client.

        This function starts the client and logs a message to the console.
        """
        await super().start()

        try:
            await cache.ping()
        except (CacheBackendInteractionError, TimeoutError):
            sys.exit(log.critical("Can't connect to RedisDB! Exiting..."))

        async with SQLite3Connection() as conn:
            await conn.execute(constants.SQLITE3_TABLES, script=True)

        await load_all_modules(self)

        log.info(
            "Korone running with Hydrogram v%s (Layer %s) started on @%s. Hi!",
            hydrogram.__version__,
            layer,
            self.me.username,
        )

    async def stop(self):
        """
        Stop the client.

        This function stops the client and logs a message to the console.
        """
        await super().stop()
        log.info("Korone stopped.")
