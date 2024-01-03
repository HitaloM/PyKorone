# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

from dataclasses import dataclass
from pathlib import Path

import hydrogram
from hydrogram import Client
from hydrogram.enums import ParseMode
from hydrogram.raw.all import layer

from korone import constants
from korone.modules import load_all_modules

from .utils.logging import log


@dataclass
class AppParameters:
    """
    Parameters for :obj:`hydrogram.Client`.

    This class represents the parameters for initializing the bot.
    """

    api_id: str
    """The API ID of the bot."""
    api_hash: str
    """The API hash of the bot."""
    bot_token: str
    """The bot token of the bot."""
    ipv6: bool = True
    """Whether to use IPv6."""
    name: str = constants.CLIENT_NAME
    """The name of the bot."""
    workers: int = constants.WORKERS
    """The number of workers to use."""


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

    Methods
    -------
    start()
        Starts the client.
    stop()
        Stops the client.
    """

    def __init__(self, parameters: AppParameters):
        self.parameters = parameters
        self.me: hydrogram.types.User

        super().__init__(
            name=self.parameters.name,
            api_id=self.parameters.api_id,
            api_hash=self.parameters.api_hash,
            bot_token=self.parameters.bot_token,
            workers=self.parameters.workers,
            ipv6=self.parameters.ipv6,
            parse_mode=ParseMode.HTML,
            workdir=str(Path(__file__).parent.parent),
            sleep_threshold=180,
        )

    async def start(self) -> None:
        """
        Start the client.

        This function starts the client and logs a message to the console.
        """
        await super().start()

        load_all_modules(self)

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
