# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from pathlib import Path

from cashews import Cache

__version__ = "1.0.4"

cache = Cache()
cache.setup("redis://localhost", client_side=True)

app_dir = Path(__file__).parent.parent.parent
