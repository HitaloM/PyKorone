# Sophie Telegram Bot

Modern, fast Telegram chat manager bot.

## Requirements

- Python 3.12+
- Poetry
- MongoDB
- Redis

### Additional requirements for openSUSE to build dependencies

- libicu-devel
- gcc-c++
- python313-devel
- gcc13

## Quick start (for development, not production)

1. Install dependencies:
    - poetry install
2. Configure:
    - cp data/config.example.env data/config.env
    - Edit data/config.env (TOKEN, APP_ID/APP_HASH, Mongo/Redis, OWNER_ID, etc.).
3. Run:
    - poetry run python -m sophie_bot

Optional: set MODE in config.env to scheduler to run the scheduler mode.

## In-house developed libraries

- [ASS](https://gitlab.com/SophieBot/ass) — Argument searcher of Sophie
- [STFU](https://gitlab.com/SophieBot/stf) — Sophie Text Formatting Utility

Wiki: https://sophie-wiki.orangefox.tech/

License: GNU AGPLv3
