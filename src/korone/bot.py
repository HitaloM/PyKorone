# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

from dataclasses import dataclass

import hydrogram
from hydrogram import Client
from hydrogram.enums import ParseMode
from hydrogram.raw.all import layer

from korone import constants

from .utils.logging import log


@dataclass
class AppParameters:
    """Parameters for :obj:`hydrogram.Client`.

    Parameters
    ----------
    api_id : str
        The Telegram API ID.
    api_hash : str
        The Telegram API hash.
    bot_token : str
        The Telegram bot token.
    ipv6 : bool, optional
        Whether to use IPv6. Default is True.
    name : str, optional
        The client name. Default is constants.CLIENT_NAME.
    workers : int, optional
        The number of workers to be used by client. Default is constants.WORKERS.
    """

    api_id: str
    api_hash: str
    bot_token: str
    ipv6: bool = True
    name: str = constants.CLIENT_NAME
    workers: int = constants.WORKERS


class Korone(Client):
    """
    Represents a bot named Korone.

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
            sleep_threshold=180,
        )

    async def start(self) -> None:
        """Starts the client."""
        await super().start()
        log.info(
            "Korone running with Hydrogram v%s (Layer %s) started on @%s. Hi!",
            hydrogram.__version__,
            layer,
            self.me.username,
        )

    async def stop(self):
        """Stops the client."""
        await super().stop()
        log.info("Korone stopped.")
