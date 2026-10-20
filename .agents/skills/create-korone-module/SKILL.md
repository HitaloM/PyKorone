---
name: create-korone-module
description: Create and register a new loadable top-level PyKorone module under src/korone/modules. Not for edits to an existing module.
---

# Create a PyKorone Module

Read the [manifest and loader contract](../py-korone-development/references/modules.md),
`src/korone/modules/metadata.py`, and the closest live module by behavior. `web` demonstrates commands/callbacks;
`stickers` demonstrates middleware lifecycle; `inline` demonstrates registry integration. Inspect only the relevant case.

## Assembly

- Define commands/events, public or internal visibility, and any persistence, transport, hooks, stats, exports, or inline
  contributions the feature actually requires. Create only those files and manifest fields.
- Expose one `manifest: ModuleManifest` from the package and add its slug to the ordered `korone.modules.MODULES` tuple.
  Use a named router when handling Telegram updates; register handler classes through `ModuleManifest.handlers`.
- For commands/callbacks, follow [handler contracts](../py-korone-development/references/handlers-aiogram.md).
  Use typed arguments and callbacks, owner checks, and response helpers. FSM requires an explicit runtime storage design
  because the default dispatcher disables it.
- Keep module middleware under `middlewares/`, export its entry points, and register it in a declared `pre_setup()`
  hook. Give module jobs startup/shutdown observers. Keep processing, parsing, transport, and persistence outside middleware.
- Localize public metadata, argument descriptions, and output with
  [localization-workflow](../localization-workflow/SKILL.md). Read the
  [UI reference](../py-korone-development/references/text-ui.md) for structured descriptions/output and the
  [persistence reference](../py-korone-development/references/persistence.md) when adding stored data.

## Validation

With controlled configuration, import the package and pass it to `LoadedModule.from_module(...)`. In an isolated
dispatcher, check router inclusion and handler registration. Check only the arguments, authorization, hooks, exports,
stats, persistence, or inline behavior introduced by the module. Hooks may run concurrently within a phase; verify
resource ownership without assuming sibling order. Complete catalog validation and relevant Ruff/Pyright checks.
