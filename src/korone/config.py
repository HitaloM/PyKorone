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

    Attributes
    ----------
    config : (dict[str, Any])
        The configuration template used to create the configuration file if it does not exist.
    """

    def __init__(self):
        self.config: dict[str, Any] = constants.DEFAULT_CONFIG_TEMPLATE

    def init(self, cfgpath: str = constants.DEFAULT_CONFIG_PATH) -> None:
        """
        Initialize the configuration module.

        This function initializes the configuration module. It loads the configuration file
        from the filesystem and creates it if it does not exist.

        Parameters
        ----------
        cfgpath : str, optional
            The path to the configuration file, by default constants.CONFIG_PATH.
        """

        log.info("Initializing configuration module")
        log.debug("Using path %s", cfgpath)

        config_path = Path(cfgpath)
        if not config_path.is_file():
            log.info("Could not find configuration file")
            try:
                log.info("Creating configuration file")
                config_path.write_text(rtoml.dumps(self.config), encoding="utf-8")
            except OSError as err:
                log.critical("Could not create configuration file: %s", err)

        self.config = rtoml.loads(config_path.read_text(encoding="utf-8"))

    def get(self, section: str, option: str, fallback: str = "") -> str:
        """
        Retrieve a configuration option.

        This function retrieves a configuration option from the configuration file.

        Parameters
        ----------
        section : str
            The name of the section in the configuration file.
        option : str
            The name of the option within the section.
        fallback : str, optional
            The default value to be returned if the option is not found, defaults to "".

        Returns
        -------
        str
            The value of the specified option. If the option is not found, returns the default
            value.
        """
        return self.config.get(section, {}).get(option, fallback)
