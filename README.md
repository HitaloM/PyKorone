<div align="center">
  <img src="https://github.com/HitaloM/PyKorone/assets/40531911/d971b149-72b5-4411-9ea5-21b5c44e5061" width="112" alt="PyKorone logo">
  <h1>PyKorone</h1>
  <p>A modular, open-source Telegram bot for communities.</p>

[![Telegram](https://img.shields.io/badge/Telegram-@PyKorone-26A5E4?logo=telegram&logoColor=white)](https://t.me/PyKorone)
[![aiogram](https://img.shields.io/badge/aiogram-3-2CA5E0)](https://github.com/aiogram/aiogram)
[![License](https://img.shields.io/badge/License-AGPL--3.0-663399)](LICENSE)

</div>

PyKorone brings media downloads, Last.fm tools, sticker management, and group utilities to Telegram private chats and
groups. Open [@PyKorone](https://t.me/PyKorone) and send `/help` to explore the available commands.

[Features](#features) · [Podman deployment](#podman) · [Local development](#development) · [Configuration](#configuration)

## Features

| Area | What it does |
| --- | --- |
| Media | Downloads shared content from Twitter, Bluesky, Instagram, Pinterest, Reddit, and TikTok. |
| Last.fm | Shows listening activity, album and artist information, compatibility, and album collages. |
| Stickers | Copies stickers and supported media into personal packs, with pack and sticker management. |
| Lookups | Searches GSMArena device specifications, looks up IP/domain information, and normalizes URLs. |
| Groups | Provides per-chat command controls, administrator utilities, and localized help. |
| Privacy | Links to the configured privacy policy and exports available stored data. |

Features are independently registered modules. The runtime uses aiogram, PostgreSQL with async SQLAlchemy, Redis,
gettext localization, structured logging, and optional Sentry reporting.

## Podman

The deployment stack runs the bot, PostgreSQL, Redis, and a local Telegram Bot API server through rootless Podman
Quadlet and systemd. An optional Cloudflare Tunnel supports webhooks. All services communicate on a private container
network; the stack publishes no host ports.

### Requirements

- Linux with a user systemd manager and cgroup v2.
- Podman 5.4 or newer, including Quadlet and rootless networking dependencies.
- Subordinate UID/GID ranges configured for the deployment user in `/etc/subuid` and `/etc/subgid`.
- Git and Make. Python and the bot's system dependencies are installed in the container image.

### Setup

Clone the repository and run the following as your regular deployment user:

```sh
git clone https://github.com/HitaloM/PyKorone.git
cd PyKorone
cp data/config.example.env data/config.env
cp data/podman.example.env data/podman.env
chmod 600 data/config.env data/podman.env
```

Edit the copied files before starting:

| File | Required values |
| --- | --- |
| `data/config.env` | `TOKEN`, your bot token from @BotFather. |
| `data/podman.env` | `TELEGRAM_API_ID` and `TELEGRAM_API_HASH`, application credentials from [my.telegram.org](https://my.telegram.org/apps). |

The application credentials are separate from the bot token. Keep unused optional settings commented out.

```sh
make podman-install
make podman-up
make podman-logs
```

Installation links the Quadlet files and installs configuration; starting the stack builds the image and provisions
storage. The bot waits for PostgreSQL and Redis healthchecks, then applies pending database migrations.
Keep the checkout at its installed path and use a separate checkout and deployment user for each instance.

### Operations

| Action | Command or guide |
| --- | --- |
| Stop the stack, keeping volumes | `make podman-down` |
| Rebuild after code changes | `make podman-build`, then `systemctl --user restart korone-bot.service` |
| Refresh configuration | `make podman-config`, then restart the affected services; see [updates](deploy/README.md#updates). |
| Start at boot | `systemctl --user enable korone.target` and `loginctl enable-linger "$USER"` |
| Set up Cloudflare Tunnel | [Webhook configuration](#configuration) and [tunnel startup](deploy/README.md#optional-tunnel) |
| Inspect failures or storage | [Diagnostics](deploy/README.md#diagnostics) and [storage ownership](deploy/README.md#storage-and-security) |

The [deployment guide](deploy/README.md) explains service lifecycle, secrets, shared storage, and troubleshooting.

## Development

For a bot running directly on your machine, install the Python version in [.python-version](.python-version), uv,
PostgreSQL, and Redis. Media/sticker features also need `ffmpeg` and `ffprobe`; WHOIS lookups need `whois`.
Catalog updates need GNU gettext tools, including `msgattrib`.

From the repository root:

```sh
uv sync --locked
cp data/config.example.env data/config.env
chmod 600 data/config.env
```

Set `TOKEN` and configure `DB_URL`, `REDIS_HOST`, and `REDIS_PORT` for your local services. Create the PostgreSQL user
and database referenced by `DB_URL`; the example uses `korone` for both. Apply the schema and start the bot:

```sh
make db_upgrade
uv run python -m korone
```

Normal startup also applies pending migrations. Without `WEBHOOK_DOMAIN`, the bot uses long polling. Startup and
shutdown discard pending Telegram updates, so use a separate bot token and services for development.

### Validation and contributions

```sh
uv run ruff check
uv run ruff format --check
uv run pyright
```

The project has no automated test suite. Validate behavior changes with focused deterministic reproductions.
For user-facing text changes, update catalogs with `make update_lang`, manually review translations, and run
`make compile_lang`.

Read [AGENTS.md](AGENTS.md) for project contracts and workflow routing. The
[development skill](.agents/skills/py-korone-development/SKILL.md) links to architectural references by responsibility;
[domain skills](.agents/skills) cover bug fixes, new modules/providers, localization, and commits.

## Configuration

[data/config.example.env](data/config.example.env) documents bot settings;
[src/korone/config.py](src/korone/config.py) defines their defaults and validation. Environment variables override
`data/config.env`. Quadlet supplies its own database, Redis, Bot API, storage, and web-server settings.

| Setting | Purpose |
| --- | --- |
| `OWNER_ID`, `OPERATORS` | Telegram user IDs for operator access. The configured owner is included automatically. |
| `MODULES_LOAD`, `MODULES_NOT_LOAD` | JSON arrays selecting registered modules. `["*"]` loads all; exclusions take precedence. |
| `DEFAULT_LOCALE` | Default message locale, initially `en_US`. |
| `LASTFM_KEY` | Enables Last.fm API requests. |
| `SENTRY_URL` | Enables Sentry error reporting. |
| `WEBHOOK_DOMAIN`, `WEBHOOK_SECRET`, `WEBHOOK_PATH` | Public webhook origin, request secret, and path. Leave the domain unset for polling. |

For the optional Podman tunnel, set `TUNNEL_TOKEN` in `data/podman.env`, route its public HTTPS hostname to
`http://korone-bot:9669`, and set the matching `WEBHOOK_DOMAIN`, `WEBHOOK_SECRET`, and `WEBHOOK_PATH` in `data/config.env`.
Refresh configuration and restart/start the services as described in the [tunnel guide](deploy/README.md#optional-tunnel).

## License

PyKorone is licensed under the [GNU Affero General Public License v3.0](LICENSE).
