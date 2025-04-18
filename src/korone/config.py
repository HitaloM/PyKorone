# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

from __future__ import annotations

from pathlib import Path
from typing import Any, Self, TypeVar, cast

from tomlkit import dump, loads

from . import constants
from .utils.logging import logger

T = TypeVar("T")


class ConfigError(Exception):
    """Exception raised for configuration-related errors."""

    pass


class ConfigManager:
    """Manages the configuration for the application.

    This class implements the Singleton pattern to ensure only one instance
    is created throughout the application lifecycle.
    """

    __slots__ = ("_initialized", "config")
    _instance: Self | None = None

    def __new__(cls, cfgpath: str = constants.DEFAULT_CONFIG_PATH) -> Self:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, cfgpath: str = constants.DEFAULT_CONFIG_PATH) -> None:
        """Initialize the ConfigManager with the specified configuration path.

        Args:
            cfgpath: Path to the configuration file
        """
        if hasattr(self, "_initialized") and self._initialized:
            return

        logger.info("Initializing configuration manager")
        logger.debug("Using path %s", cfgpath)

        config_path = Path(cfgpath)
        self._ensure_config(config_path)

        self.config: dict[str, Any] = loads(config_path.read_text(encoding="utf-8"))
        self._initialized = True

    def _ensure_config(self, config_path: Path) -> None:
        """Ensure that the configuration directory and file exist.

        Args:
            config_path: Path to the configuration file
        """
        self._ensure_directory(config_path.parent)
        self._ensure_file(config_path)

    @staticmethod
    def _ensure_directory(directory: Path) -> None:
        """Create the directory if it doesn't exist.

        Args:
            directory: Directory path to ensure exists

        Raises:
            ConfigError: If directory creation fails
        """
        if not directory.exists():
            logger.info("Creating configuration directory at %s", directory)
            try:
                directory.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                logger.critical("Failed to create directory %s: %s", directory, e)
                msg = f"Failed to create directory {directory}"
                raise ConfigError(msg) from e

    @staticmethod
    def _ensure_file(config_path: Path) -> None:
        """Create the configuration file with default template if it doesn't exist.

        Args:
            config_path: Path to the configuration file

        Raises:
            ConfigError: If file creation fails
        """
        if not config_path.is_file():
            logger.info("Creating configuration file at %s", config_path)
            try:
                with config_path.open("w", encoding="utf-8") as file:
                    dump(constants.DEFAULT_CONFIG_TEMPLATE, file)
            except OSError as e:
                logger.critical("Failed to create file %s: %s", config_path, e)
                msg = f"Failed to create file {config_path}"
                raise ConfigError(msg) from e

    @classmethod
    def get(cls, section: str, option: str, fallback: T | None = None) -> T | Any:
        """Get a configuration value.

        Args:
            section: Configuration section
            option: Option name within the section
            fallback: Default value if option is not found

        Returns:
            Configuration value or fallback

        Raises:
            ConfigError: If ConfigManager hasn't been initialized
        """
        if cls._instance is None:
            msg = "ConfigManager has not been initialized"
            raise ConfigError(msg)

        value = cls._instance.config.get(section, {}).get(option, fallback)
        return cast(T, value)
