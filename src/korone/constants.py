# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

import os
from pathlib import Path
from typing import Any

CLIENT_NAME: str = "Korone"
"""The default client name.

:type: str
"""

WORKERS: int = 24
"""The default number of workers.

:type: int
"""

XDG_CONFIG_HOME: str = os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))
"""
The XDG_CONFIG_HOME environment variable.
Where user-specific configurations should be written (analogous to /etc).

:type: str
"""

XDG_DATA_HOME: str = os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local/share"))
"""
The XDG_DATA_HOME environment variable.
Where user-specific data files should be written (analogous to /usr/share).

:type: str
"""

DEFAULT_CONFIG_PATH: str = f"{XDG_CONFIG_HOME}/korone/korone.toml"
"""The default path to the config file.

:type: str
"""


DEFAULT_CONFIG_TEMPLATE: dict[str, Any] = {
    "hydrogram": {
        "API_ID": "",
        "API_HASH": "",
        "BOT_TOKEN": "",
        "USE_IPV6": False,
        "WORKERS": 24,
    },
    "korone": {
        "SUDOERS": [918317361],
    },
}
"""
The default config template.

:type: dict[str, typing.Any]

Examples
---------
>>> from korone import constants
>>> print(constants.DEFAULT_CONFIG_TEMPLATE)
{
    "hydrogram": {
        "API_ID": "",
        "API_HASH": "",
        "BOT_TOKEN": "",
        "USE_IPV6": False,
        "WORKERS": 24,
    },
    "korone": {
        "SUDOERS": [918317361],
    },
}
"""

DEFAULT_DBFILE_PATH: str = f"{XDG_DATA_HOME}/korone/korone.sqlite"
"""The default path to the database file.

:type: str
"""
