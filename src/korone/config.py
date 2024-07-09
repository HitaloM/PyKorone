# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from pathlib import Path
from typing import Any

from tomlkit import dump, loads

from korone import constants
from korone.utils.logging import log


class ConfigError(Exception):
    pass


class ConfigManager:
    __slots__ = ("config",)
    _instance: "ConfigManager | None" = None

    def __new__(cls, *args, **kwargs):
        if not isinstance(cls._instance, cls):
            cls._instance = super().__new__(cls)

        return cls._instance

    def __init__(self, cfgpath: str = constants.DEFAULT_CONFIG_PATH):
        log.info("Initializing configuration module")
        log.debug("Using path %s", cfgpath)

        config_path = Path(cfgpath)
        self._create_config_directory(config_path)
        self._create_config_file(config_path)

        self.config: dict[str, Any] = loads(config_path.read_text(encoding="utf-8"))

    @staticmethod
    def _create_config_directory(config_path: Path):
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
        if config_path.is_file():
            return

        log.info("Could not find configuration file")
        try:
            log.info("Creating configuration file")
            with config_path.open("w", encoding="utf-8") as file:
                dump(constants.DEFAULT_CONFIG_TEMPLATE, file)
        except OSError as err:
            log.critical("Could not create configuration file: %s", err)
            msg = "Could not create configuration file"
            raise ConfigError(msg) from err

    @classmethod
    def get(cls, section: str, option: str, fallback: str = "") -> Any:
        if cls._instance is None:
            msg = "ConfigManager instance has not been initialized"
            raise ConfigError(msg)

        return cls._instance.config.get(section, {}).get(option, fallback)
