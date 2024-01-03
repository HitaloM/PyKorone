# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

import os
from pathlib import Path

CLIENT_NAME: str = "Korone"
"""The default client name."""

WORKERS: int = 24
"""The default number of workers."""

XDG_CONFIG_HOME: str = os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))
"""
The XDG_CONFIG_HOME environment variable.
Where user-specific configurations should be written (analogous to /etc).
"""

XDG_DATA_HOME: str = os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local/share"))
"""
The XDG_DATA_HOME environment variable.
Where user-specific data files should be written (analogous to /usr/share).
"""

DEFAULT_CONFIG_PATH: str = f"{XDG_CONFIG_HOME}/korone/korone.toml"
"""The default path to the config file."""

DEFAULT_DBFILE_PATH: str = f"{XDG_DATA_HOME}/korone/korone.sqlite"
"""The default path to the database file."""
