# Copilot instructions for Korone

## Architecture overview
- Entry point: src/korone/__main__.py initializes DB, loads modules, wires middlewares, and starts aiogram polling.
- Bot/Dispatcher live in src/korone/__init__.py (Redis FSM storage, optional Bot API server).
- Module system: src/korone/modules/__init__.py imports modules, includes each module `router`, registers `__handlers__`, and runs optional `__pre_setup__`/`__post_setup__` hooks (see src/korone/modules/help/__init__.py).
- Handlers subclass `KoroneMessageHandler`/`KoroneCallbackQueryHandler`/`KoroneMessageCallbackQueryHandler` in src/korone/utils/handlers.py and register via `register()`.

## Middleware data flow
- SaveChatsMiddleware (src/korone/middlewares/save_chats.py) populates `data["chat_db"]`, `data["user_db"]`, `data["user_in_group"]` and keeps chats/users/topics synced.
- ChatContextMiddleware adds `data["chat"]` (ChatContext with `db_model`), used by handlers.
- LocalizationMiddleware (src/korone/middlewares/localization.py) selects locale from DB + Redis cache; use gettext helpers from src/korone/utils/i18n.py (domain `korone`, locales/).

## Data/storage conventions
- Async SQLAlchemy with SQLite by default: engine in src/korone/db/engine.py; sessions via `session_scope()` in src/korone/db/session.py.
- Prefer repository helpers in src/korone/db/repositories/* for chat/language/disable logic.
- `ChatModel.chat_id` is the Telegram ID; `ChatModel.id` is the internal DB PK. Use repo helpers like `get_by_chat_id()` when starting from Telegram data.

## Project-specific patterns
- Commands use CMDFilter (src/korone/filters/cmd.py) with prefixes from CONFIG (default `/!`); don’t use aiogram’s Command filter directly.
- User-facing text is built with stfu-tg `Doc`/`Template` (example: src/korone/modules/help/handlers/start_pm.py) instead of manual string concatenation.
- Argument parsing uses ass-tg (ArgsMiddleware is installed in __main__.py); define handler args via `handler_args()`.

## Developer workflows
- Configuration is loaded from data/config.env via src/korone/config.py (`CONFIG` controls modules, prefixes, redis/db).
- Localization workflow uses Makefile targets: `extract_lang`, `update_lang`, `compile_lang` (all run via `uv run pybabel`).
- Lint/format: ruff settings live in ruff.toml (line length 120, future annotations enforced).
