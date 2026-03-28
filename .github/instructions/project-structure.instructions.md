---
description: "Use when understanding Korone project structure, tracing feature flows, locating code for bug fixes, and navigating application plus infrastructure files (modules, middlewares, repositories, i18n, Docker, Alembic, and env config)."
name: "Korone Project Structure"
---

# Korone Project Structure

- These guidelines are strong preferences for architecture navigation and code discovery.
- Use this file to map ownership quickly before editing code.

## Repository Layout

- `src/korone/`: main bot application code.
- `alembic/`: schema migrations.
- `alembic.ini`: Alembic configuration and migration script location.
- `locales/`: translation source and compiled files (`.pot`, `.po`, `.mo`).
- `data/`: environment and runtime configuration files.
- `docker-compose.yml`: local/runtime service topology.
- `Dockerfile`: container image build flow.
- `Makefile`: common developer and operations entrypoints.
- `.github/instructions/`: project guidance for coding and tooling behavior.

## Application Layers (`src/korone/`)

- `args/`: command argument helpers.
- `db/models/`: SQLAlchemy models.
- `db/repositories/`: data access layer (handlers should call repositories, not raw ORM).
- `filters/`: aiogram filters.
- `middlewares/`: request/context pipeline.
- `modules/`: feature packages and command handlers.
- `utils/`: shared utilities (handlers base classes, i18n, exceptions, etc.).

## Core Entry Points

- `src/korone/__main__.py`: startup/bootstrap flow.
- `src/korone/__init__.py`: shared globals and app-level exports.
- `src/korone/config.py`: runtime settings and environment bindings.
- `src/korone/logger.py`: structured logging setup.

## Module Convention (`src/korone/modules/<feature>/`)

- Typical structure: `__init__.py`, `handlers/`, `utils/`, and optional `callbacks.py`, `stats.py`, `export.py`.
- `__init__.py` is the module contract and should expose metadata such as `__module_name__`, `__module_description__`, and `__handlers__`.
- Handler classes should be grouped under `handlers/` and registered through the module router.

## Where To Look First

- Command bug: start in `src/korone/modules/<feature>/handlers/` and trace to repositories if data is involved.
- Data bug: inspect matching model in `src/korone/db/models/`, then repository methods in `src/korone/db/repositories/`.
- Middleware behavior: inspect `src/korone/middlewares/` and handler flags consumed by middlewares.
- Translation issue: inspect call sites using `_()` / `l_()` and corresponding files in `locales/`.
- Infra/runtime issue: inspect `docker-compose.yml`, `Dockerfile`, `data/*.env`, `alembic.ini`, and `Makefile` targets.

## Code Tracing Flow

- Entry path: `__main__.py` -> dispatcher/router setup -> module handlers.
- Handler path: module handler -> business logic/utilities -> repository -> database model.
- Middleware path: incoming event -> middleware chain -> handler execution.

## Change Planning Rules

- Before editing, identify the owning layer (middleware, module handler, repository, model, or utility).
- Keep changes within the correct layer boundaries and avoid cross-layer shortcuts.
- For cross-cutting tasks, touch the minimum set of layers required and document why multiple layers changed.

## Related Instructions

- Coding patterns: `.github/instructions/python-coding-style.instructions.md`.
- Tooling workflows: `.github/instructions/development-tooling.instructions.md`.
