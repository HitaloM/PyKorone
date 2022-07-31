# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2020-2022 Hitalo <https://github.com/HitaloSama>

import pytomlpp


class Config:
    config = pytomlpp.loads(open("config.toml", "r").read())
    table = "korone"

    def get_config(self, key: str, table: str = table):
        return self.config[table][key]


config = Config()
