# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2020-2022 Hitalo <https://github.com/HitaloSama>

from .languages import (
    LANGUAGES,
    change_chat_lang,
    get_chat_lang,
    get_chat_lang_info,
    get_string,
    get_strings,
    get_strings_dec,
)
from .messages import (
    get_args,
    get_args_str,
    get_command,
    get_full_command,
    need_args_dec,
)

__all__ = (
    "get_command",
    "get_args_str",
    "get_args",
    "get_full_command",
    "need_args_dec",
    "LANGUAGES",
    "change_chat_lang",
    "get_chat_lang",
    "get_chat_lang_info",
    "get_string",
    "get_strings",
    "get_strings_dec",
)
