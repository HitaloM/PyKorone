# PyKorone

<img src="https://github.com/HitaloM/PyKorone/assets/40531911/d971b149-72b5-4411-9ea5-21b5c44e5061" width="96" alt="PyKorone logo">

[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Telegram](https://img.shields.io/badge/Telegram-blue.svg?logo=telegram)](https://t.me/PyKorone)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)

PyKorone is a modular Telegram bot built with [aiogram 3](https://github.com/aiogram/aiogram), PostgreSQL, Redis, and gettext-based localization. It supports long polling and webhook deployments with independently loadable feature packages. It has been in development since [January 2, 2021](https://telegra.ph/file/ce181caad7447b7f48cdc.png).

## Contents

- [Features](#features)
- [Requirements](#requirements)
- [Getting Started](#getting-started)
- [Configuration](#configuration)
- [Docker Compose](#docker-compose)
- [Development](#development)
- [Localization](#localization)
- [License](#license)

## Features

- Modular runtime: feature packages are loaded independently at startup.
- Flexible deployment: choose long polling or webhook mode based on your environment.
- Persistence: PostgreSQL for data storage, Redis for state and caching.
- Localization: gettext-based i18n with a manual review workflow.
- Error reporting: Sentry integration for production environments.

## Requirements

- Python 3.14+
- PostgreSQL
- Redis
- A Telegram bot token

## Getting Started

```bash
git clone https://github.com/HitaloM/PyKorone.git
cd PyKorone
uv sync
cp data/config.example.env data/config.env
# Edit data/config.env with your credentials
uv run python -m korone
```

If `webhook_domain` is not set in `config.env`, the bot starts in long polling mode.

## Configuration

Copy [data/config.example.env](data/config.example.env) to [data/config.env](data/config.env) and fill in the required fields:

```env
TOKEN="YOUR_TOKEN"
USERNAME="your_bot_username"
OWNER_ID=483808054
```

All available settings, including database, Redis, webhook, module loading, and Sentry options, are defined in [src/korone/config.py](src/korone/config.py).

## Docker Compose

The repository includes a Docker Compose setup for local development and self-hosted deployments.

```bash
cp data/config.example.env data/config.env
docker compose up -d --build
```

The default stack includes the following services:

| Service | Description |
| --- | --- |
| `telegram-bot-api` | Local Telegram Bot API server used by the bot runtime |
| `postgres` | PostgreSQL database |
| `redis` | Redis instance for state and caching |
| `korone-bot` | The bot container itself |
| `tunnel` | Optional Cloudflare tunnel, enabled with `--profile tunnel` |

The stack reads [data/config.env](data/config.env) for the bot and [data/docker.env](data/docker.env) for the local Bot API container. Adjust both files before starting.

Useful commands:

```bash
# Follow bot logs
docker compose logs -f korone-bot

# Stop all services
docker compose down

# Start with Cloudflare tunnel
docker compose --profile tunnel up -d --build
```

## Development

Makefile targets for common tasks:

| Command | Description |
| --- | --- |
| `make locale` | Refreshes extraction, updates catalogs, and compiles translations |
| `make update_lang` | Updates gettext catalogs after string changes |
| `make compile_lang` | Rebuilds compiled `.mo` files |
| `make db_revision m="..."` | Creates a new Alembic migration |
| `make db_upgrade` | Applies pending database migrations |
| `make db_downgrade` | Rolls back the last database migration |

## Localization

When user-facing strings change, follow this workflow to keep translations in sync:

1. Run `make update_lang`
2. Review changes in `locales/pt_BR/LC_MESSAGES/korone.po`
3. Resolve any fuzzy entries in the same commit
4. Run `make compile_lang`

## License

PyKorone is licensed under the [GNU Affero General Public License v3.0 (AGPLv3)](LICENSE), a copyleft license approved by the [Free Software Foundation](https://www.fsf.org/) and the [Open Source Initiative](https://opensource.org/). See the full license text on the [GNU site](https://www.gnu.org/licenses/agpl-3.0.html).
