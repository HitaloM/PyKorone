# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2020-2022 Hitalo <https://github.com/HitaloSama>

import pytomlpp


class Config:
    config = pytomlpp.loads(open("config.toml", "r").read())
    table = "korone"

    def get_config(self, key: str, table: str = table):
        try:
            config = self.config[table][key]
        except KeyError:
            return None
        return config


config = Config()
