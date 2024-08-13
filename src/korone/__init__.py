# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from pathlib import Path

from cashews import Cache

from .utils.i18n import create_i18n_instance

__version__ = "1.0.2"

cache = Cache()
cache.setup("redis://localhost", client_side=True)

app_dir = Path(__file__).parent.parent.parent
locales_dir: Path = app_dir / "locales"

i18n = create_i18n_instance(locales_dir)
