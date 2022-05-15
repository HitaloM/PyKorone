# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2020-2022 Amano Team

import html
import re


def cleanhtml(raw_html):
    cleanr = re.compile("<.*?>")
    return re.sub(cleanr, "", raw_html)


def escape_definition(definition):
    for key, value in definition.items():
        if isinstance(value, str):
            definition[key] = html.escape(cleanhtml(value))
    return definition
