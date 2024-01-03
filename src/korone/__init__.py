# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

import subprocess
from pathlib import Path

from hairydogm.i18n import I18n

result = subprocess.run(
    "git rev-parse --short HEAD && git rev-list --count HEAD", shell=True, capture_output=True
)

commit_hash, commit_count = result.stdout.decode("utf-8").strip().split("\n")

__version__ = f"{commit_hash} ({commit_count})"

app_dir = Path(__file__).parent.parent.parent
locales_dir: Path = app_dir / "locales"

i18n = I18n(path=locales_dir)
