# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from __future__ import annotations

from pathlib import Path
from typing import Any

from tomlkit import dump, loads

from korone import constants
from korone.utils.logging import logger


class ConfigError(Exception):
    pass


class ConfigManager:
    __slots__ = ("config", "initialized")
    _instance: ConfigManager | None = None

    def __new__(cls, *args, **kwargs) -> ConfigManager:
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, cfgpath: str = constants.DEFAULT_CONFIG_PATH) -> None:
        if hasattr(self, "initialized") and self.initialized:
            return

        logger.info("Initializing configuration module")
        logger.debug("Using path %s", cfgpath)

        config_path = Path(cfgpath)
        self._create_config_directory(config_path)
        self._create_config_file(config_path)

        self.config: dict[str, Any] = loads(config_path.read_text(encoding="utf-8"))
        self.initialized = True

    @staticmethod
    def _create_config_directory(config_path: Path) -> None:
        if not config_path.parent.exists():
            logger.info("Creating configuration directory")
            try:
                config_path.parent.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                logger.critical("Could not create configuration directory: %s", e)
                msg = "Could not create configuration directory"
                raise ConfigError(msg) from e

    @staticmethod
    def _create_config_file(config_path: Path) -> None:
        if not config_path.is_file():
            logger.info("Creating configuration file")
            try:
                with config_path.open("w", encoding="utf-8") as file:
                    dump(constants.DEFAULT_CONFIG_TEMPLATE, file)
            except OSError as e:
                logger.critical("Could not create configuration file: %s", e)
                msg = "Could not create configuration file"
                raise ConfigError(msg) from e

    @classmethod
    def get(cls, section: str, option: str, fallback: str = "") -> Any:
        if not cls._instance:
            msg = "ConfigManager instance has not been initialized"
            raise ConfigError(msg)

        return cls._instance.config.get(section, {}).get(option, fallback)
