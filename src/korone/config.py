# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from pathlib import Path
from typing import Any

import rtoml

from korone import constants
from korone.utils.logging import log


class ConfigError(Exception):
    """
    Represents an error that occurs while loading or saving the configuration.

    This exception is raised when an error occurs while loading or saving the configuration.
    """

    pass


class ConfigManager:
    """
    Configuration manager class.

    This class is responsible for managing the configuration settings of the application.

    Parameters
    ----------
    cfgpath : str, optional
        The path to the configuration file, by default constants.CONFIG_PATH.

    Attributes
    ----------
    config : dict[str, typing.Any]
        The configuration template used to create the configuration file if it does not exist.
    """

    __slots__ = ("config",)
    _instance: "ConfigManager | None" = None

    def __new__(cls, *args, **kwargs):
        """
        Create a new instance of the class.

        This method overrides the built-in __new__ method to implement the Singleton pattern.
        If an instance of the class does not already exist, it creates a new one and stores it
        in the class variable _instance. If an instance already exists, it returns the existing
        instance.

        Parameters
        ----------
        *args : tuple
            Variable length argument list.
        **kwargs : dict
            Arbitrary keyword arguments.

        Returns
        -------
        ConfigManager
            The existing instance of the class if it exists, otherwise a new instance.
        """
        if not isinstance(cls._instance, cls):
            cls._instance = super().__new__(cls)

        return cls._instance

    def __init__(self, cfgpath: str = constants.DEFAULT_CONFIG_PATH):
        """
        Initialize the configuration manager.

        This method initializes the configuration manager by creating the configuration directory
        and configuration file if they do not already exist. It then loads the configuration file
        into memory.

        Parameters
        ----------
        cfgpath : str, optional
            The path to the configuration file, by default constants.CONFIG_PATH.
        """
        log.info("Initializing configuration module")
        log.debug("Using path %s", cfgpath)

        config_path = Path(cfgpath)
        self._create_config_directory(config_path)
        self._create_config_file(config_path)

        self.config: dict[str, Any] = rtoml.loads(config_path.read_text(encoding="utf-8"))

    @staticmethod
    def _create_config_directory(config_path: Path):
        """
        Create the configuration directory.

        This method creates the configuration directory if it does not already exist.

        Parameters
        ----------
        config_path : Path
            The path to the configuration file.

        Raises
        ------
        ConfigError
            If an error occurs while creating the configuration directory.
        """
        if config_path.parent.exists():
            return

        log.info("Could not find configuration directory")
        try:
            log.info("Creating configuration directory")
            config_path.parent.mkdir(parents=True, exist_ok=True)
        except OSError as err:
            log.critical("Could not create configuration directory: %s", err)
            msg = "Could not create configuration directory"
            raise ConfigError(msg) from err

    @staticmethod
    def _create_config_file(config_path: Path):
        """
        Create the configuration file.

        This method creates the configuration file if it does not already exist.

        Parameters
        ----------
        config_path : Path
            The path to the configuration file.

        Raises
        ------
        ConfigError
            If an error occurs while creating the configuration file.
        """
        if config_path.is_file():
            return

        log.info("Could not find configuration file")
        try:
            log.info("Creating configuration file")
            rtoml.dump(constants.DEFAULT_CONFIG_TEMPLATE, config_path, pretty=True)
        except OSError as err:
            log.critical("Could not create configuration file: %s", err)
            msg = "Could not create configuration file"
            raise ConfigError(msg) from err

    @classmethod
    def get(cls, section: str, option: str, fallback: str = "") -> Any:
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
        Any
            The value of the specified option. If the option is not found, returns the default
            value.
        """
        if cls._instance is None:
            msg = "ConfigManager instance has not been initialized"
            raise ConfigError(msg)

        return cls._instance.config.get(section, {}).get(option, fallback)
