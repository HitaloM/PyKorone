# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2020-2022 Amano Team
#
# This file is part of Korone (Telegram Bot)

import glob
import re
from typing import Dict

import yaml

from korone.utils.langs import Langs

strings: Dict = {}


def get_languages(only_codes: bool = False):
    if only_codes:
        return strings.keys()

    if len(strings.keys()) < 1:
        load_languages()

    return Langs(**strings)


def load_languages() -> None:
    for string_file in glob.glob("korone/locales/*.yml"):
        language_code = re.match(r"korone/locales/(.+)\.yml$", string_file)[1]
        strings[language_code] = yaml.safe_load(open(string_file, "r"))
