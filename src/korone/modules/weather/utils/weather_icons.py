# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

STATUS_EMOJIS: dict[int, str] = {
    0: "⛈",
    1: "⛈",
    2: "⛈",
    3: "⛈",
    4: "⛈",
    5: "🌨",
    6: "🌨",
    7: "🌨",
    8: "🌨",
    9: "🌨",
    10: "🌨",
    11: "🌧",
    12: "🌧",
    13: "🌨",
    14: "🌨",
    15: "🌨",
    16: "🌨",
    17: "⛈",
    18: "🌧",
    19: "🌫",
    20: "🌫",
    21: "🌫",
    22: "🌫",
    23: "🌬",
    24: "🌬",
    25: "🌨",
    26: "☁️",
    27: "🌥",
    28: "🌥",
    29: "⛅️",
    30: "⛅️",
    31: "🌙",
    32: "☀️",
    33: "🌤",
    34: "🌤",
    35: "⛈",
    36: "🔥",
    37: "🌩",
    38: "🌩",
    39: "🌧",
    40: "🌧",
    41: "❄️",
    42: "❄️",
    43: "❄️",
    44: "n/a",
    45: "🌧",
    46: "🌨",
    47: "🌩",
}


def get_status_emoji(status_code: int) -> str:
    return STATUS_EMOJIS.get(status_code, "n/a")
