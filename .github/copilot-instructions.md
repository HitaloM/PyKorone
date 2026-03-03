# Copilot Instructions — PyKorone

## Big Picture (how the bot is wired)
- Entry point is `src/korone/__main__.py`: it configures middleware, initializes DB, auto-runs Alembic migrations, ensures bot user in DB, then loads modules dynamically.
- Runtime has two modes:
  - Webhook mode when `WEBHOOK_DOMAIN` is set (`aiohttp` app + `SimpleRequestHandler`).
  - Long polling otherwise.
- Module boundary is `src/korone/modules/*`; module loading is centralized in `src/korone/modules/__init__.py` via `MODULES`, `__handlers__`, and optional hooks `__pre_setup__` / `__post_setup__`.

## Data Flow and Persistence
- Chat/user context is persisted at middleware layer (`SaveChatsMiddleware`) before handlers; it populates `data["chat_db"]`, `data["user_db"]`, etc.
- `ChatContextMiddleware` builds `data["chat"]` (typed chat context) for handler classes.
- Repositories in `src/korone/db/repositories/` are the write/read boundary; use them instead of raw SQL in handlers.
- SQLAlchemy session pattern is `session_scope()` from `src/korone/db/session.py` (commit/rollback handled in context manager).
- Do not introduce `create_all`; schema evolution is Alembic-first and startup already calls `migrate_db_if_needed()`.

## Handler and Module Conventions (project-specific)
- Prefer class-based handlers from `src/korone/utils/handlers.py`:
  - `KoroneMessageHandler`
  - `KoroneCallbackQueryHandler`
  - `KoroneMessageCallbackQueryHandler`
- Typical pattern: implement `filters()` and register through module `__handlers__` (see `src/korone/modules/language/__init__.py`).
- Use `aiogram` flags because middlewares consume them (example: `@flags.disableable(name="start")` in `src/korone/modules/help/handlers/start_group.py`).
- For module metadata/help cards, follow `__module_name__`, `__module_description__`, `__module_info__`, `__module_emoji__` patterns.

## i18n and Text
- i18n is mandatory for user-facing text:
  - Use `gettext as _` for runtime strings.
  - Use `lazy_gettext as l_` for metadata evaluated later (module labels/descriptions).
- Core i18n implementation is `src/korone/utils/i18n.py` (`I18nNew`, locale stats, display helpers).
- Locale selection logic is in `LocalizationMiddleware` and chat language is stored on `ChatModel.language_code`.

## Dev Workflows You Should Use
- Environment/deps: `uv sync`
- Run bot locally: `uv run python -m korone`
- Lint/format: `uv run ruff check . --fix --preview --unsafe-fixes` and `uv run ruff format .`
- Type-check: `uv run pyright`
- DB migrations: `make db_upgrade`, `make db_revision m="message"`, `make db_downgrade`
- Translations: `make extract_lang`, `make update_lang`, `make compile_lang`
- Full local stack: `docker compose up -d` (postgres, redis, telegram-bot-api, bot)

## Integrations and Operational Notes
- Redis is used for FSM storage (`src/korone/__init__.py`), PostgreSQL for persistent data, Alembic for schema history.
- Optional local Bot API server is controlled by `BOTAPI_SERVER`; production API fallback is automatic.
- Optional Sentry is enabled when `SENTRY_URL` is set.
- Config comes from `data/config.env` via `pydantic-settings` (`src/korone/config.py`); prefer adding new settings there.
