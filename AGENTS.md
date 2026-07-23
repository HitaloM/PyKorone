# PyKorone Codex Instructions

## Repository Context

PyKorone is a modular Telegram bot built with Python 3.14+, aiogram 3.x, PostgreSQL, Redis, SQLAlchemy async, Alembic, Ruff, Pyright, uv, and gettext catalogs.

Keep repository guidance small and durable here. Use the domain skills under `.agents/skills/` for detailed workflows.

## Default Workflow

- Read the nearest existing implementation before editing; follow local patterns over new abstractions.
- Keep edits scoped to the requested behavior and avoid unrelated formatting churn.
- Use `rg` or `rg --files` for searches.
- Use `uv` for project commands; do not introduce pip-only, poetry, or pipenv workflows.
- Do not revert user changes or dirty worktree changes unless explicitly asked.
- Prefer focused validation. Run broader checks when touching shared handlers, repositories, migrations, module loading, localization, or tooling.

## Common Commands

- Install dependencies: `uv sync --locked`
- Run the bot: `uv run python -m korone`
- Ruff lint: `uv run ruff check`
- Ruff format: `uv run ruff format`
- Type check: `uv run pyright`
- Update locale catalogs: `make update_lang`
- Compile locale catalogs: `make compile_lang`
- Create Alembic revision: `make db_revision m="message"`
- Apply migrations: `make db_upgrade`

## Required Skills

- Use `.agents/skills/python-code-standards/SKILL.md` when generating or reviewing Python under `src/korone/`.
- Use `.agents/skills/issue-fixer/SKILL.md` when diagnosing or fixing reported bugs, regressions, exceptions, failing checks, or unexpected behavior.
- Use `.agents/skills/aiogram-project-patterns/SKILL.md` when touching aiogram runtime, routers, handlers, filters, callback data, middleware, polling, or webhook code.
- Use `.agents/skills/bot-handler-development/SKILL.md` when creating or modifying handlers, ASS arguments, STFU responses, handler flags, callbacks, FSM flows, or handler ID/data access.
- Use `.agents/skills/korone-modules-plugin-contract/SKILL.md` when creating or editing top-level module package files under `src/korone/modules/*/__init__.py`.
- Use `.agents/skills/medias-module-patterns/SKILL.md` for any change under `src/korone/modules/medias/`.
- Use `.agents/skills/development-tooling/SKILL.md` when changing uv, Ruff, Pyright, pre-commit, Alembic, Babel, Docker, Makefile, runtime bootstrap, or workflow configuration.
- Use `.agents/skills/localization-manual-translation/SKILL.md` whenever user-facing strings or locale catalogs change.

## Project Rules

- New and edited Python functions must have complete type annotations using modern syntax.
- Prefer project handler bases from `korone.utils.handlers` over raw function-based aiogram handlers.
- Keep database access behind repository classes and async SQLAlchemy sessions.
- Use structured logging through `korone.logger.get_logger`.
- Keep module package metadata and loader contracts stable.
- When strings shown to users change, update and manually review gettext catalogs in the same change.
