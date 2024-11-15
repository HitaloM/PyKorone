# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from __future__ import annotations

from pathlib import Path
from typing import Any, Self

from tomlkit import dump, loads

from . import constants
from .utils.logging import logger


class ConfigError(Exception):
    pass


class ConfigManager:
    __slots__ = ("_initialized", "config")
    _instance: Self | None = None

    def __new__(cls, cfgpath: str = constants.DEFAULT_CONFIG_PATH) -> Self:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, cfgpath: str = constants.DEFAULT_CONFIG_PATH) -> None:
        if hasattr(self, "_initialized") and self._initialized:
            return

        logger.info("Initializing configuration manager")
        logger.debug("Using path %s", cfgpath)

        config_path = Path(cfgpath)
        self._ensure_config(config_path)

        self.config: dict[str, Any] = loads(config_path.read_text(encoding="utf-8"))
        self._initialized = True

    def _ensure_config(self, config_path: Path) -> None:
        self._ensure_directory(config_path.parent)
        self._ensure_file(config_path)

    @staticmethod
    def _ensure_directory(directory: Path) -> None:
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
    def get(cls, section: str, option: str, fallback: Any = None) -> Any:
        if cls._instance is None:
            msg = "ConfigManager has not been initialized"
            raise ConfigError(msg)
        return cls._instance.config.get(section, {}).get(option, fallback)
