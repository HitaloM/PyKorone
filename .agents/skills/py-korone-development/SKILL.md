---
name: py-korone-development
description: Implement or review PyKorone code and project tooling. Use for changes under src/korone or to uv, Ruff, Pyright, Alembic, Babel, Docker, Makefile, and runtime bootstrap; load only the references matching the affected area. Do not use as the primary workflow for bug diagnosis, a new media platform, or a new top-level module.
---

# PyKorone Development

Implement changes by treating the current repository as authoritative and loading only the technical references needed for the affected boundary.

## Workflow

1. Inspect `git status` and preserve unrelated worktree changes.
2. Read the nearest existing implementation before designing the change.
3. Read each relevant reference completely before editing:
   - Any Python change: [references/python.md](references/python.md)
   - Handlers, aiogram, callbacks, filters, flags, ASS arguments, STFU, FSM, or middleware:
     [references/handlers-aiogram.md](references/handlers-aiogram.md)
   - Module manifests, package metadata, loader registration, hooks, stats, or exports:
     [references/modules.md](references/modules.md)
   - Any existing code under `src/korone/modules/medias/`:
     [references/medias.md](references/medias.md)
   - Dependencies, uv, Ruff, Pyright, pre-commit, Alembic, Babel, Docker, Makefile, or runtime bootstrap:
     [references/tooling.md](references/tooling.md)
4. Follow local implementations over generic examples or stale assumptions.
5. Keep the patch scoped and keep shared contracts stable unless the request explicitly changes them.
6. Use `localization-workflow` whenever user-facing strings or gettext catalogs change.
7. Run focused validation first, then broaden checks when changing shared handlers, repositories, migrations, module loading, localization, or tooling.

## Validation Baseline

- Run `uv run ruff check <changed paths>` for Python changes.
- Run `uv run pyright` when typing, public APIs, handlers, repositories, or shared runtime code change.
- Run the specialized checks required by the selected references.
- Report commands, outcomes, and anything that could not be verified.
