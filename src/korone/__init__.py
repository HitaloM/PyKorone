# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import subprocess
from pathlib import Path

from cashews import Cache

from korone.utils.i18n import I18nNew as I18n
from korone.utils.logging import log

__version__ = "1.0.0"

cache = Cache()
cache.setup("redis://localhost", client_side=True)

app_dir = Path(__file__).parent.parent.parent
locales_dir: Path = app_dir / "locales"


def create_i18n_instance(locales_dir: Path) -> I18n:
    """
    Create an instance of the I18n class.

    This function creates an instance of the I18n class using the specified locales directory.
    If the locales directory does not exist, the function will compile the locales using pybabel
    before creating the I18n instance.

    Parameters
    ----------
    locales_dir : Path
        The path to the locales directory.

    Returns
    -------
    I18n:
        An instance of the I18n class.
    """
    try:
        return I18n(path=locales_dir)
    except RuntimeError:
        log.info("Compiling locales...")
        subprocess.run(
            f"pybabel compile -d '{locales_dir}' -D bot",
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        return I18n(path=locales_dir)


i18n = create_i18n_instance(locales_dir)
