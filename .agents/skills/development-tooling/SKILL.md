---
name: development-tooling
description: Use when editing development tooling configuration or workflows in this repository, including uv, Ruff, pre-commit, Pyright, Alembic, Babel locale tasks, Docker build/runtime setup, Makefile targets, pyproject.toml, ruff.toml, .python-version, Dockerfile, docker-compose.yml, alembic files, and runtime bootstrap.
---

# Development Tooling Rules for PyKorone

## Scope

Apply these rules when changing repository tooling, developer workflow, build pipeline, migrations, localization automation, or runtime bootstrap.

## Package and Environment Management

- uv is the required workflow tool for dependency and command execution.
- Use uv-based commands in project automation and docs: `uv sync --locked`, `uv run python`, `uv run alembic`, and `uv run pybabel`.
- Do not introduce parallel package manager workflows such as pip-only, poetry, or pipenv unless there is an explicit repository migration decision.

## Linting, Formatting, and Type Checking

- Ruff is the required formatter and linter for this repository.
- Keep line length and lint policy aligned with `ruff.toml`.
- When changing Ruff behavior, verify compatibility with pre-commit hooks.
- Preserve pre-commit hook intent: Ruff check with fix and preview flags, then Ruff format.
- Keep Pyright as a local static type checker dependency.
- Avoid broad ignore patterns for type checking; prefer targeted and justified suppressions.

Treat uv and Ruff alignment as hard rules, not optional style preferences.

## Migration Tooling

- Preserve Alembic as the migration system and keep migration flow consistent with `alembic.ini`, `alembic/env.py`, and runtime migration orchestration in `src/korone/db/utils.py`.
- Prefer Makefile database targets for workflow consistency: `db_upgrade`, `db_downgrade`, `db_revision`, and `db_stamp`.
- Keep database URL handling compatible with environment-first resolution used by Alembic and runtime startup.

## Localization Tooling

- Preserve existing Makefile locale flow and extraction keys.
- Keep merge and compile sequence stable: `extract_lang`, `update_lang`, `compile_lang`.
- Avoid changing localization command semantics unless all dependent locale artifacts are updated accordingly.
- Follow `.agents/skills/localization-manual-translation/SKILL.md` when strings or locale catalogs change.

## Docker and Runtime Tooling

- Keep Docker build flow aligned with uv lockfile usage and reproducible sync; builder stages should use `uv sync --locked`.
- Keep runtime startup contract stable: entrypoint executes `python -m korone`.
- If runtime dependencies are changed, verify impact on media and utility tooling already installed in the runtime image.

## Cross-File Consistency Rules

When changing one area, check related files in the same change:

- Ruff policy changes: `ruff.toml` and `.pre-commit-config.yaml`.
- Migration flow changes: `alembic.ini`, `alembic/env.py`, `src/korone/db/utils.py`, and Makefile db targets.
- Runtime startup changes: `src/korone/__init__.py`, `src/korone/__main__.py`, `docker-compose.yml`, and `Dockerfile`.
- Dependency updates: `pyproject.toml` and `uv.lock`.
- Python version changes: `.python-version`, `pyproject.toml`, `Dockerfile`, and README requirements.

## Avoid These Anti-Patterns

- Adding a second formatter or linter pipeline that conflicts with Ruff.
- Replacing uv commands in automation with ad hoc interpreter or pip commands.
- Introducing migration execution paths that bypass established Alembic orchestration.
- Changing Makefile tooling targets without checking downstream usage and docs.
- Altering Docker runtime startup semantics without keeping bot bootstrap behavior intact.

## Change Checklist

- Confirm commands in Makefile still work after tooling edits.
- Confirm pre-commit hooks still reflect Ruff policy.
- Confirm migration commands and runtime migration detection still align.
- Confirm dependency and lockfile changes are synchronized.
- Confirm Docker build and runtime remain reproducible with current toolchain assumptions.
