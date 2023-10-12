# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2020-2022 Hitalo M. <https://github.com/HitaloM>

from pathlib import Path

import pytomlpp


class Config:
    config = pytomlpp.loads(Path("config.toml").read_text())
    table = "korone"

    def get_config(self, key: str, table: str = table):
        try:
            config = self.config[table][key]
        except KeyError:
            return None
        return config


config = Config()
