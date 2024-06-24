# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import os
from pathlib import Path
from typing import Any

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
        "DEEPL_KEY": "",
        "LASTFM_KEY": "",
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

SQLITE3_TABLES: str = """
CREATE TABLE IF NOT EXISTS Users (
    id INTEGER PRIMARY KEY,
    first_name VARCHAR(64) NOT NULL,
    last_name VARCHAR(64),
    username VARCHAR(32),
    language VARCHAR(5) NOT NULL DEFAULT "en",
    registry_date INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS Groups (
    id INTEGER PRIMARY KEY,
    title VARCHAR(64) NOT NULL,
    username VARCHAR(32),
    type VARCHAR(16) NOT NULL,
    language VARCHAR(5) NOT NULL DEFAULT "en",
    registry_date INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS Afk (
    id INTEGER PRIMARY KEY,
    state BIT,
    reason VARCHAR(64)
);
CREATE TABLE IF NOT EXISTS Commands (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER,
    command VARCHAR(32),
    state BIT,
    FOREIGN KEY(chat_id) REFERENCES Groups(id)
);
CREATE TABLE IF NOT EXISTS LastFM (
    id INTEGER PRIMARY KEY,
    username VARCHAR(255)
);
CREATE TABLE IF NOT EXISTS StickerPack (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    num INTEGER DEFAULT 1,
    type VARCHAR(16)
);
"""
"""The default SQLite3 tables.

:type: str
"""

TRANSLATIONS_URL: str = "https://weblate.amanoteam.com/projects/korone/"
"""The URL to the translations platform.

:type: str
"""

GITHUB_URL: str = "https://github.com/HitaloM/PyKorone"
"""The URL to the GitHub repository.

:type: str
"""

TELEGRAM_URL: str = "https://t.me/PyKorone"
"""The URL to the Telegram channel.

:type: str
"""
