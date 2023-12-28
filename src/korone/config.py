# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

from pathlib import Path
from typing import Any

import rtoml

from korone import constants

from .utils.logging import log


class ConfigManager:
    """
    Configuration manager class.

    This class is responsible for managing the configuration settings of the application.

    Attributes:
        config (dict[str, Any]): The configuration settings.

    Methods:
        __init__(): Initializes the ConfigManager object.
        init(cfgpath: str = constants.CONFIG_PATH) -> None: Initializes the configuration module.
        get(section: str, option: str, fallback: str = "") -> str: Retrieves a configuration option

    """

    def __init__(self):
        self.config: dict[str, Any] = {
            "hydrogram": {
                "API_ID": "",
                "API_HASH": "",
                "BOT_TOKEN": "",
                "USE_IPV6": False,
                "WORKERS": 24,
            },
            "korone": {
                "SUDOERS": [918317361],
            },
        }

    def init(self, cfgpath: str = constants.CONFIG_PATH) -> None:
        """
        Initializes the configuration module.

        Args:
            cfgpath (str): The path to the configuration file. Defaults to constants.CONFIG_PATH.
        """

        log.info("Initializing configuration module")
        log.debug("Using path %s", cfgpath)

        if not Path(cfgpath).is_file():
            log.info("Could not find configuration file")
            try:
                log.debug("Creating configuration file")
                with Path(cfgpath).open("w", encoding="utf-8") as configfile:
                    configfile.write(rtoml.dumps(self.config))
            except OSError as err:
                log.critical("Could not create configuration file: %s", err)

        with Path(cfgpath).open("r", encoding="utf-8") as configfile:
            self.config = rtoml.loads(configfile.read())

    def get(self, section: str, option: str, fallback: str = "") -> str:
        """
        Retrieves a configuration option.

        Args:
            section (str): The section of the configuration.
            option (str): The option to retrieve.
            fallback (str): The fallback value if the option is not found. Defaults to "".

        Returns:
            str: The value of the configuration option.
        """
        return self.config.get(section, {}).get(option, fallback)
