---
name: create-korone-module
description: Create and register a new loadable top-level PyKorone module under src/korone/modules. Use for new module packages, manifests, Telegram entry points, optional runtime providers, persistence boundaries, and loader wiring. Do not use for ordinary edits to an existing module.
---

# Create a PyKorone Module

Create one complete loadable module from current repository patterns. Do not rely on a static scaffold: inspect the live
module and metadata contracts before deciding which files and manifest fields the new module needs.

## Workflow

1. Read [py-korone-development](../py-korone-development/SKILL.md) and its
   [Python](../py-korone-development/references/python.md),
   [handlers and aiogram](../py-korone-development/references/handlers-aiogram.md), and
   [modules](../py-korone-development/references/modules.md), and
   [text UI](../py-korone-development/references/text-ui.md) references, plus any other relevant reference.
2. Read `src/korone/modules/metadata.py`, `src/korone/modules/__init__.py`, and the closest current module by behavior:
   - simple command;
   - callbacks or pagination;
   - database-backed;
   - external service;
   - inline query provider;
   - internal runtime.
3. Define the boundary:
   - commands and incoming events;
   - user-visible output;
   - callbacks and FSM;
   - module-specific middleware and its lifecycle;
   - external dependencies;
   - database and cache needs;
   - public or internal visibility;
   - lifecycle hooks, stats, or exports.
4. Create only the package structure required by that boundary and expose exactly one `manifest: ModuleManifest` from
   its `__init__.py`. Adapt its shape from the nearest live module rather than copying a generic template.
5. Add the module slug to the ordered `korone.modules.MODULES` tuple at the intended load position.
6. Add a named router and project handler classes only when the module receives Telegram updates. Keep handlers focused
   on orchestration and register their classes through `ModuleManifest.handlers`.
7. Put custom module middleware classes in a `middlewares/` subpackage, export intentional entry points from its
   `__init__.py`, and register them only in `pre_setup()` through `ModuleManifest.scripts`.
8. Keep processing managers, repositories, external transport, and parsing outside middleware and handlers.
9. Define typed callback data and authorize user-bound interactions.
10. Declare lifecycle hooks, stats, exports, and inline-query integration through the corresponding manifest fields;
    avoid import-time registration and other side effects.
11. Add help metadata and disableable flags when appropriate.
12. Localize public package metadata, argument descriptions, and runtime output with `localization-workflow`.
13. Add and manually review an Alembic migration when persistence changes.

## Validation

- Import the module package.
- Verify `LoadedModule.from_module(...)` accepts its manifest.
- Verify loader position, router inclusion, and handler registration.
- Verify commands, arguments, flags, callbacks, authorization checks, and FSM states in scope.
- Verify repository, cache, external-service, hook, stats, export, and inline-query contracts in scope.
- When localized strings changed, update, manually review, and compile catalogs.
- Run focused Ruff checks and Pyright.
