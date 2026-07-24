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

- Use `.agents/skills/py-korone-development/SKILL.md` when implementing or reviewing code under `src/korone/` or changing project tooling. Load only the references matching the affected area.
- Use `.agents/skills/issue-fixer/SKILL.md` when diagnosing or fixing reported bugs, regressions, exceptions, failing checks, or unexpected behavior.
- Use `.agents/skills/localization-workflow/SKILL.md` whenever user-facing strings or gettext catalogs change.
- Use `.agents/skills/add-media-platform/SKILL.md` only when adding a completely new supported media platform. Use `issue-fixer` for bugs and `py-korone-development` for refactors of existing platforms.
- Use `.agents/skills/create-korone-module/SKILL.md` only when creating and registering a new top-level loadable module. Use `py-korone-development` for ordinary edits to existing modules.

## Project Rules

- New and edited Python functions must have complete type annotations using modern syntax.
- Prefer project handler bases from `korone.utils.handlers` over raw function-based aiogram handlers.
- Keep database access behind repository classes and async SQLAlchemy sessions.
- Use structured logging through `korone.logger.get_logger`.
- Keep module package metadata and loader contracts stable.
- When strings shown to users change, update and manually review gettext catalogs in the same change.
