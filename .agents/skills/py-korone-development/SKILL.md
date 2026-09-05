---
name: py-korone-development
description: Implement or review PyKorone code and project tooling. Use for changes under src/korone or to uv, Ruff, Pyright, Alembic, Babel, Docker, Makefile, and runtime bootstrap; load only the references matching the affected area. Do not use as the primary workflow for bug diagnosis, a new media platform, or a new top-level module.
---

# PyKorone Development

Implement changes by treating the current repository as authoritative and loading only the technical references needed for the affected boundary.

## Workflow

1. Inspect `git status` and preserve unrelated worktree changes.
2. Read the nearest implementation and the relevant references below before designing the change. Preserve domain
   behavior while converging on the shared contracts described in those references.
3. Read each relevant reference completely before editing:
   - Any Python change: [references/python.md](references/python.md)
   - Handlers, aiogram, callbacks, filters, flags, project arguments, FSM, or middleware:
     [references/handlers-aiogram.md](references/handlers-aiogram.md)
   - Text UI expressions, compiler behavior, module descriptions, or message/caption payload rendering:
     [references/text-ui.md](references/text-ui.md)
   - Module manifests, package metadata, loader registration, hooks, stats, or exports:
     [references/modules.md](references/modules.md)
   - Any existing code under `src/korone/modules/medias/`:
     [references/medias.md](references/medias.md)
   - Dependencies, uv, Ruff, Pyright, pre-commit, Alembic, Babel, Docker, Makefile, or runtime bootstrap:
     [references/tooling.md](references/tooling.md)
4. Use the canonical boundary for the responsibility. Keep domain-specific exceptions local rather than building a
   universal framework. Record shared decisions and their rationale once in the relevant skill reference; keep
   `AGENTS.md` focused on general rules and routing, and the README on basic developer setup.
5. Keep the patch scoped and keep shared contracts stable unless the request explicitly changes them.
6. Use `localization-workflow` whenever user-facing strings or gettext catalogs change.
7. Run focused validation first, then broaden checks when changing shared handlers, repositories, migrations, module loading, localization, or tooling.

## Validation Baseline

- This project has no automated test suite. Do not create tests, test files, test fixtures, or introduce a test framework unless the user explicitly requests it.
- Validate behavior with the smallest deterministic reproduction suited to the change.
- Run `uv run ruff check <changed paths>` for Python changes.
- Run `uv run pyright` when typing, public APIs, handlers, repositories, or shared runtime code change.
- Run the specialized checks required by the selected references. Import affected modules because static checks
  cannot detect every runtime annotation or inheritance problem.
- For cross-cutting changes, load affected manifests/handlers in an isolated dispatcher, exercise locale/entity
  boundaries and resource lifecycles in scope, and use deterministic inputs without production service writes.
- Report commands, outcomes, and anything that could not be verified.
