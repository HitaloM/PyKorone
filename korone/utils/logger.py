# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2020-2022 Hitalo M. <https://github.com/HitaloM>

import logging
import sys

LEVEL: int = logging.INFO

if "--debug" in sys.argv:
    LEVEL: int = logging.DEBUG

logging.basicConfig(
    level=LEVEL,
    format="%(name)s.%(funcName)s | %(levelname)s | %(message)s",
    datefmt="[%X]",
)

log: logging.Logger = logging.getLogger(__name__)
