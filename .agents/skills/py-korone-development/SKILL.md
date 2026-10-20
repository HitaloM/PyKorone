---
name: py-korone-development
description: Implement or review PyKorone code and project tooling. For bugs, new media providers, or new loadable modules, use the specialized workflow first.
---

# PyKorone Development

Use the current code as the contract source. Read the nearest implementation and select references by the responsibility
being changed, rather than loading every reference for every Python edit.

| Affected responsibility | Reference |
| --- | --- |
| Python typing, runtime annotations, or abstraction choices | [python.md](references/python.md) |
| Handlers, typed command arguments, callbacks, flags, permissions, middleware | [handlers-aiogram.md](references/handlers-aiogram.md) |
| Structured output, UI compiler, entities, or lazy descriptions | [text-ui.md](references/text-ui.md) |
| Manifests, loader, hooks, stats, exports, or inline providers | [modules.md](references/modules.md) |
| Repositories, models, ID namespaces, transactions, or migrations | [persistence.md](references/persistence.md) |
| Existing media pipeline or provider | [medias.md](references/medias.md) |
| HTTP, subprocesses, file ownership, caches, startup, or shutdown | [runtime.md](references/runtime.md) |
| Dependencies, uv, Ruff, Pyright, Makefile, Containerfile, or Quadlet | [tooling.md](references/tooling.md) |

Keep feature logic in its owning module and use shared integration boundaries. Add abstractions only for concrete shared
policies. Record a changed architectural contract and its rationale in its owning reference, without adding a rule for
every local implementation detail. Use [localization-workflow](../localization-workflow/SKILL.md) for visible strings.

## Validation

Follow the no-new-tests policy in `AGENTS.md`. For behavior changes, use a focused deterministic reproduction with local
inputs and controlled dependencies. Run `uv run ruff check <paths>` and `uv run ruff format --check <paths>` for Python
edits; run `uv run pyright` for changed types, APIs, handlers, repositories, or shared runtime code.

Select additional checks from the affected reference. Import/load checks matter for runtime annotations, inheritance,
manifests, and registration, but imports of `korone` construct settings and runtime clients. Use controlled configuration
and an isolated dispatcher when needed; do not start the bot to validate an ordinary edit.
Report the changed behavior, validation results, and material limits.
