"""PyKorone langs utils."""
# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2020-2022 Amano Team
#
# This file is part of Korone (Telegram Bot)

from typing import List

chat_languages = {}
user_languages = {}

__all__: List[str] = ["Langs", "get_languages", "load_languages"]
