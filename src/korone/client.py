# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import shutil
import tempfile
import time
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import hydrogram
from hydrogram import Client
from hydrogram.enums import ParseMode
from hydrogram.errors import MessageIdInvalid, MessageNotModified
from hydrogram.raw.all import layer

from korone import __version__, app_dir, cache, constants
from korone.database.sqlite import SQLite3Connection
from korone.modules import load_all_modules
from korone.utils.logging import log

if TYPE_CHECKING:
    from hydrogram.types import User


@dataclass(frozen=True, slots=True)
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
    name: str = "Korone"
    """The name of the :class:`hydrogram.Client`.

    :type: str
    """
    workers: int = 24
    """The number of workers to be used by the :class:`hydrogram.Client`.

    :type: int
    """


class Korone(Client):
    """
    Represents Korone.

    This class represents Korone, this class inherits from the :obj:`hydrogram.Client` class.
    It is used to modify Client functions if necessary and provide additional functionality
    specific to Korone.

    Parameters
    ----------
    parameters : AppParameters
        The parameters for initializing the bot.
    """

    __slots__ = ("me", "parameters")

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
            max_concurrent_transmissions=2,
        )

    async def start(self) -> None:
        """
        Start the client.

        This function starts the client and performs the necessary initialization steps.
        It establishes a connection to the SQLite3 database, executes the required SQL scripts,
        loads all the modules, and logs a message to the console indicating the successful start.

        If the client was rebooted, it checks for any cached reboot data and updates the
        corresponding message.
        """
        await super().start()

        async with SQLite3Connection() as conn:
            await conn.execute(constants.SQLITE3_TABLES, script=True)
            await conn.vacuum()

        await load_all_modules(self)

        log.info(
            "PyKorone %s running with Hydrogram v%s (Layer %s) started on @%s. Hi!",
            __version__,
            hydrogram.__version__,
            layer,
            self.me.username,
        )

        cache_key = "korone-reboot"
        if reboot_data := await cache.get(cache_key):
            with suppress(MessageNotModified, MessageIdInvalid, KeyError):
                chat_id = reboot_data["chat_id"]
                message_id = reboot_data["message_id"]
                time_elapsed = round(time.time() - reboot_data["time"], 2)
                text = f"Rebooted in {time_elapsed} seconds."

                await self.edit_message_text(chat_id=chat_id, message_id=message_id, text=text)

            await cache.delete(cache_key)

    async def stop(self) -> None:
        """
        Stop the client.

        This function stops the client, logs a message to the console, and moves the `tmp` and
        `downloads` directories to a temporary directory before deleting them. This is done
        because deleting a directory can be faster than deleting many individual files, as the
        operating system only needs to update the parent directory once to remove the directory
        entry, rather than updating it for each individual file deletion.

        The `tempfile.TemporaryDirectory()` is used to create a temporary directory which is
        automatically deleted when the `with` block is exited, effectively deleting all files
        that were moved into it.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            for path in ("tmp", "downloads"):
                with suppress(FileNotFoundError):
                    shutil.move(Path(app_dir / path).as_posix(), tmp_dir)

        await super().stop()
        log.info("PyKorone stopped.")
