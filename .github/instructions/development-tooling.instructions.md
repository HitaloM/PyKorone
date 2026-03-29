---
name: development-tooling
description: "Use when editing development tooling configuration or workflows in this repository, including uv, Ruff, pre-commit, Pyright, Alembic, Babel locale tasks, and Docker build/runtime setup."
applyTo: "{pyproject.toml,uv.lock,ruff.toml,.pre-commit-config.yaml,Makefile,Dockerfile,docker-compose.yml,alembic.ini,alembic/**/*.py,src/korone/db/utils.py,src/korone/__main__.py,src/korone/__init__.py}"
---

# Development Tooling Rules for PyKorone

## Scope

Apply these rules when changing repository tooling, developer workflow, build pipeline, migrations, or localization automation.

## Package and Environment Management

- Keep uv as the standard workflow tool for dependency and command execution.
- Prefer uv-based commands in project automation and docs:
  - uv sync --locked
  - uv run python
  - uv run alembic
  - uv run pybabel
- Do not introduce parallel package manager workflows (pip-only, poetry, pipenv) unless the project is explicitly migrating.

## Linting, Formatting, and Type Checking

- Ruff is the canonical formatter and linter for this repository.
- Keep line length and lint policy aligned with ruff.toml.
- When changing Ruff behavior, verify compatibility with pre-commit hooks.
- Preserve pre-commit hook intent:
  - ruff-check with fix and preview flags
  - ruff-format
- Keep Pyright as a local static type checker dependency.
- Avoid broad ignore patterns for type checking; prefer targeted and justified suppressions.

## Migration Tooling (Alembic)

- Preserve Alembic as the migration system and keep migration flow consistent with:
  - alembic.ini
  - alembic/env.py
  - runtime migration orchestration in src/korone/db/utils.py
- Prefer Makefile database targets for workflow consistency:
  - db_upgrade
  - db_downgrade
  - db_revision
  - db_stamp
- Keep database URL handling compatible with environment-first resolution used by Alembic and runtime startup.

## Localization Tooling (Babel)

- Preserve existing Makefile locale flow and extraction keys.
- Keep merge and compile sequence stable:
  - extract_lang
  - update_lang
  - compile_lang
- Avoid changing localization command semantics unless all dependent locale artifacts are updated accordingly.

## Docker and Runtime Tooling

- Keep Docker build flow aligned with uv lockfile usage and reproducible sync:
  - builder stage uses uv sync --locked
- Keep runtime startup contract stable:
  - entrypoint executes python -m korone
- If runtime dependencies are changed, verify impact on media and utility tooling already installed in runtime image.

## Cross-File Consistency Rules

When changing one area, check related files in the same change:

- Ruff policy changes:
  - ruff.toml
  - .pre-commit-config.yaml
- Migration flow changes:
  - alembic.ini
  - alembic/env.py
  - src/korone/db/utils.py
  - Makefile db targets
- Runtime startup changes:
  - src/korone/__init__.py
  - src/korone/__main__.py
  - docker-compose.yml
  - Dockerfile
- Dependency updates:
  - pyproject.toml
  - uv.lock

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
