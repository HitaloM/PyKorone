<div align="center">
  <img src="https://github.com/HitaloM/PyKorone/assets/40531911/d971b149-72b5-4411-9ea5-21b5c44e5061" width="112" alt="PyKorone logo">
  <h1>PyKorone</h1>
  <p>A modular, open-source Telegram bot for communities.</p>

  [![Telegram](https://img.shields.io/badge/Telegram-@PyKorone-26A5E4?logo=telegram&logoColor=white)](https://t.me/PyKorone)
  [![aiogram](https://img.shields.io/badge/aiogram-3-2CA5E0)](https://github.com/aiogram/aiogram)
  [![License](https://img.shields.io/badge/License-AGPL--3.0-663399)](LICENSE)
</div>

## Overview

PyKorone brings media processing, music integrations, sticker management, information lookup, and group utilities into a single Telegram bot. It is designed for use in private chats and groups, with interactive workflows and per-chat controls.

The project follows a modular architecture in which features are independently registered and loaded. This keeps the runtime extensible while preserving clear boundaries between modules.

## Capabilities

| Category | Description |
| --- | --- |
| Media | Retrieves content shared from Twitter, Bluesky, Instagram, Pinterest, Reddit, and TikTok. |
| Last.fm | Displays listening activity, album and artist information, user compatibility, and album collages. |
| Stickers | Creates and manages personal sticker packs from stickers and supported media. |
| Device information | Searches GSMArena and presents device specifications within Telegram. |
| Network tools | Provides IP and domain information, WHOIS queries, and URL normalization. |
| Group controls | Supports per-chat command management, administrative utilities, and localized help menus. |
| Privacy | Exposes the project's privacy policy and allows users to export their stored data. |

## Architecture

PyKorone is built on [aiogram 3](https://github.com/aiogram/aiogram) and uses asynchronous components throughout its request and data flow. Feature modules define their own handlers, metadata, exports, statistics, and lifecycle hooks where applicable.

Persistent data is managed with PostgreSQL and SQLAlchemy, while Redis provides caching and transient state. The application also includes gettext-based localization, structured logging, and error reporting through Sentry.

This separation keeps feature development isolated from the core runtime and allows modules to evolve without introducing unnecessary coupling.

## Development

Use the Python version in `.python-version` and install uv, PostgreSQL, and Redis. Features also require
`ffmpeg`/`ffprobe` for media and stickers and `whois` for domain lookups; catalog updates require gettext tools.

1. Run `uv sync --locked`.
2. Copy `data/config.example.env` to `data/config.env` and configure your bot token and services.
   [Config](src/korone/config.py) defines the available settings and defaults.
3. Run `make db_upgrade` for explicit schema setup, or let normal startup apply pending migrations.
4. Start the bot with `uv run python -m korone`.

Validate changes with `uv run ruff check`, `uv run ruff format --check`, and `uv run pyright`.
The project has no automated test suite; use focused deterministic reproductions for behavior changes.

Project rules and workflow routing live in [AGENTS.md](AGENTS.md). Detailed architectural decisions, conventions,
and validation workflows live in the [development skill and its references](.agents/skills/py-korone-development/SKILL.md)
and the other [domain skills](.agents/skills).

## Podman

The Linux deployment uses rootless [Podman Quadlet](https://docs.podman.io/en/stable/markdown/podman-systemd.unit.5.html)
with systemd, Podman 5.4 or newer, cgroup v2, and subordinate UID/GID ranges configured for your user.
Install your distribution's Podman packages, including its rootless networking and Quadlet dependencies.
Run the following commands as your regular deployment user.
For an existing Docker deployment, follow the [data migration guide](deploy/README.md#migrating-existing-docker-data)
before starting this stack.

Copy the configuration examples and replace their credential placeholders:

```sh
cp data/config.example.env data/config.env
cp data/podman.example.env data/podman.env
chmod 600 data/config.env data/podman.env
```

Set `TOKEN` in `data/config.env` and `TELEGRAM_API_ID` / `TELEGRAM_API_HASH` in `data/podman.env`.
The latter are application credentials from [my.telegram.org](https://my.telegram.org/apps), as required by the
[Bot API image](https://github.com/aiogram/telegram-bot-api#configuration), and are separate from the bot token.
The bot example documents optional settings, including owner/operator IDs, modules, integrations and media limits.
Keep optional settings commented when unused.

```sh
make podman-install
make podman-up
make podman-logs
```

Quadlet builds the image from `Containerfile`, starts PostgreSQL, Redis and the local Bot API, and provisions
shared file storage. The bot waits for PostgreSQL and Redis healthchecks before starting. Its dotenv configuration
is mounted through a Podman secret; container environment settings override service addresses and storage roots.
Without `WEBHOOK_DOMAIN`, the bot uses long polling. Startup applies pending database migrations.
The stack publishes no host ports. Keep the checkout at its installed path: Quadlet links resolve the build context
from it. Use a separate checkout and deployment user for each instance.

For startup at boot, run `systemctl --user enable korone.target` and `loginctl enable-linger "$USER"`.
Use `make podman-down` to stop the stack while preserving volumes; disable the target to prevent startup at login/boot.
After code updates, run `make podman-build` followed by `systemctl --user restart korone-bot.service`.
After configuration changes, run `make podman-config` and restart the affected services.

For the optional Cloudflare Tunnel, set `TUNNEL_TOKEN` in `data/podman.env`, configure its public hostname to forward
to `http://korone-bot:9669`, and set `WEBHOOK_DOMAIN` and `WEBHOOK_SECRET` in `data/config.env`. Then run
`make podman-config` and `systemctl --user restart korone-bot.service`, followed by
`systemctl --user start korone-tunnel.service`. The public hostname must match `WEBHOOK_DOMAIN`; the configured
`WEBHOOK_PATH` must reach the bot unchanged. For persistent tunnel startup, see the
[deployment guide](deploy/README.md#optional-tunnel).

See the [deployment guide](deploy/README.md) for Docker data migration, updates, troubleshooting and volume ownership.

## License

PyKorone is distributed under the [GNU Affero General Public License v3.0](LICENSE).
