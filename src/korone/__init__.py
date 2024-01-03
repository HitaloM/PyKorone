# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

from pathlib import Path

from hairydogm.i18n import I18n

app_dir = Path(__file__).parent.parent.parent
locales_dir: Path = app_dir / "locales"

i18n = I18n(path=locales_dir)
