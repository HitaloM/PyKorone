**Project Snapshot**
- The code targets Python 3.13 and async `hydrogram[fast]`; dependencies live in `pyproject.toml` and `tool.uv` keeps the `uv` workflow canonical.
- `src/korone/__main__.py` drives startup: it pings Redis via `utils.caching.cache`, loads config, wires Logfire logging, migrates SQLite via `constants.SQLITE3_TABLES`, then runs `Korone` inside `anyio.run` with `uvloop`.
- `src/korone/client.py` subclasses `hydrogram.Client`, loads modules, sets UI commands, schedules hourly backups, and edits reboot notifications from Redis cache.
- `korone/utils/logging.py` installs structlog + Logfire processors; respect this stack when adding loggers by using `get_logger(__name__)` or `logger = get_logger("korone")`.
- `Korone.session` in `src/` is the Telegram session file; `korone/utils/backup.py` ships it along with the SQLite DB and config.

**Runtime & Config**
- `ConfigManager.create()` ensures a TOML config at `~/.config/korone/korone.toml` based on `constants.DEFAULT_CONFIG_TEMPLATE`; do not hand-roll config parsing.
- Secrets like API keys live under `[hydrogram]` or `[korone]` sections; fetch them through `ConfigManager.get(...)` rather than reading env vars directly.
- The async `anyio.Path` helpers are used throughout (config, temp cleanup); stick to them for filesystem work to remain compatible with the `anyio` loop.
- Redis is required locally at `redis://localhost`; without it the bot exits in `pre_process()`—spin up Redis before running `python -m korone`.
- SQLite data resides at `~/.local/share/korone/korone.sqlite`; schema and VACUUM happen on boot, so migrations belong in `constants.SQLITE3_TABLES`.

**Modules & Handlers**
- Each module under `src/korone/modules/<feature>/handlers/*.py` is auto-discovered by `modules/core.py`; expose decorator-decorated functions only—no manual registration.
- Use `from korone.decorators import router` with `@router.message(...)` / `@router.callback_query(...)`; the decorator attaches `Korone*Handler` wrappers so async signatures must accept `(client, update)`.
- `BaseHandler` mixin (see `handlers/base.py`) auto-persists users/groups, handles migrations, sets the i18n locale, and wraps filter evaluation—avoid duplicating that logic in handlers.
- The custom `filters.Command` ties into `modules.core.COMMANDS` to honor per-chat disable flags; when defining multi-command handlers, list variants in a single filter call.
- Parse command payloads with `CommandObject(message).parse()` instead of manual string slicing; it respects prefixes, mentions, and magic filters.

**Localization & UI**
- The `i18n` singleton from `utils/i18n.py` loads locales from `locales/*/bot.po`; wrap user-visible strings with `_ = gettext`.
- `BaseHandler._fetch_locale` pulls language choices from the database, so make sure any manual replies use the same `_` helper within handler scope.
- `utils/commands_list.set_ui_commands` rebuilds `/start` etc per locale on boot; extend `create_bot_commands` if you add global commands.
- When adding translation strings, run `make i18n-extract`, `make i18n-update`, and `make i18n-compile` to keep `.po`/`.mo` files in sync.

**Developer Workflow**
- Install dependencies with `uv sync --all-extras --dev`; CI mirrors this via `.github/workflows/code-style.yml`.
- Run static checks locally with `uv run ruff format --check .` and `uv run ruff check .`; apply fixes using the same commands without `--check`.
- Launch the bot using `uv run python -m korone` after populating `korone.toml` and starting Redis; shutdown triggers `post_process()` to clear cache and prune `downloads/`.
- Build docs with `make docs` (Sphinx) or `make live-docs`; sources live under `docs/source/`.
- Translation assets and backups can grow large—gitignore already covers compiled `.mo` files and session files, so keep new artifacts out of version control.
