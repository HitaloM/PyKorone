---
description: "Use when running Korone development tools, including uv commands, Ruff, Pyright, Alembic migrations, localization workflows, pre-commit hooks, and Docker Compose operations."
name: "Korone Development Tooling"
---

# Korone Development Tooling

- These guidelines are strong preferences. If there is a clear technical reason to deviate, prioritize correctness and document the reason.
- Use English in instruction and customization files.
- Run Python-based CLIs through `uv run ...` to keep tooling in the project environment.
- Prefer existing `Makefile` targets when they cover the workflow.

## Search And Edit Workflow

- Use `rg` for text search and `rg --files` for file discovery.
- Use `apply_patch` for manual code edits and keep diffs minimal and scoped.
- Avoid broad formatting-only changes unrelated to the requested task.

## Lint, Format, And Type Check

- For Python changes, validate changed paths first, then expand to full-repo checks only when needed.
- Suggested order for changed paths:
  - `uv run ruff check --fix <paths>`
  - `uv run ruff format <paths>`
  - `uv run pyright <paths>`
- When validating staged/changed files comprehensively, use:
  - `uv run pre-commit run --files <files...>`
  - `uv run pre-commit run --all-files` for full-repo checks when needed.

## Database Migration Tooling

- Use Make targets for Alembic workflows:
  - `make db_revision m="short_message"`
  - `make db_upgrade`
  - `make db_downgrade`
  - `make db_stamp rev="<revision>"`
- Prefer one logical schema change per migration and verify upgrade/downgrade paths when migration files change.

## Localization Tooling

- After changing user-facing strings, run localization workflows:
  - `make locale` for the standard extract/update/compile flow
  - `make new_lang LANG=<locale>` when creating a new locale
- Keep `locales/*.po` and compiled message files in sync with source text changes.

## Container And Runtime Tooling

- Run container operations from repository root using `docker compose`.
- Prefer explicit commands (`docker compose pull`, `docker compose up -d`, `docker compose logs -f <service>`) over ad-hoc scripts.
- Use `sudo` only when required by local Docker daemon permissions.

## Safety And Reproducibility

- Prefer non-interactive commands in automated or agent-driven workflows.
- Avoid destructive git operations unless explicitly requested.
- If a command cannot be executed in the current environment, report the blocker and provide the exact command for manual execution.
