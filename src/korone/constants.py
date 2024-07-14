# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import os
from pathlib import Path
from typing import Any

XDG_CONFIG_HOME: str = os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))

XDG_DATA_HOME: str = os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local/share"))

DEFAULT_CONFIG_PATH: str = f"{XDG_CONFIG_HOME}/korone/korone.toml"

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
        "SENTRY_DSN": "",
        "DEEPL_KEY": "",
        "LASTFM_KEY": "",
    },
}

DEFAULT_DBFILE_PATH: str = f"{XDG_DATA_HOME}/korone/korone.sqlite"

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

TRANSLATIONS_URL: str = "https://weblate.amanoteam.com/projects/korone/"

GITHUB_URL: str = "https://github.com/HitaloM/PyKorone"

TELEGRAM_URL: str = "https://t.me/PyKorone"

DOCS_URL: str = "https://pykorone.readthedocs.io"
