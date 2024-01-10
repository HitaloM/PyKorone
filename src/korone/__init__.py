# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

import subprocess
from pathlib import Path

from cashews import cache

from korone.utils.i18n import I18nNew as I18n

from .utils.logging import log

result = subprocess.run(
    "git rev-parse --short HEAD && git rev-list --count HEAD", shell=True, capture_output=True
)

commit_hash, commit_count = result.stdout.decode("utf-8").strip().split("\n")

__version__ = f"{commit_hash} ({commit_count})"

app_dir = Path(__file__).parent.parent.parent
locales_dir: Path = app_dir / "locales"

cache.setup("redis://localhost", client_side=True)


def create_i18n_instance(locales_dir: Path) -> I18n:
    try:
        return I18n(path=locales_dir)
    except RuntimeError:
        log.info("Compiling locales...")
        subprocess.run(
            f"pybabel compile -d '{locales_dir}' -D bot",
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return I18n(path=locales_dir)


i18n = create_i18n_instance(locales_dir)
