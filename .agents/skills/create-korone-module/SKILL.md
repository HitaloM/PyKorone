---
name: create-korone-module
description: Create and register a new loadable top-level PyKorone module under src/korone/modules. Use for new module packages, manifests, routers, handlers, callbacks, metadata, initial repositories or service layers, and loader wiring. Do not use for ordinary edits to an existing module.
---

# Create a PyKorone Module

Create one complete loadable module that follows the current manifest, handler, localization, and loader contracts.

## Workflow

1. Read [py-korone-development](../py-korone-development/SKILL.md) and its
   [Python](../py-korone-development/references/python.md),
   [handlers and aiogram](../py-korone-development/references/handlers-aiogram.md), and
   [modules](../py-korone-development/references/modules.md) references, plus any other relevant reference.
2. Identify the closest current module by behavior:
   - simple command;
   - callbacks or pagination;
   - database-backed;
   - external service;
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
4. Create the package and one `ModuleManifest`.
5. Add the module slug to `korone.modules.MODULES` at the intended load position.
6. Keep handlers focused on Telegram orchestration.
7. Put module-specific middleware classes in a `middlewares/` subpackage, export intentional entry points from its
   `__init__.py`, and register them only in `pre_setup()` through `ModuleManifest.scripts`.
8. Keep processing managers, repositories, external transport, and parsing outside middleware and handlers.
9. Define typed callback data and authorize user-bound interactions.
10. Add help and disableable flags when appropriate.
11. Localize public package metadata, argument descriptions, and runtime output with `localization-workflow`.
12. Add and manually review an Alembic migration when persistence changes.

## Template Asset

Use [assets/module_template](assets/module_template) as an optional starting point for a simple command module. Rename
every `Example` symbol and command, copy only the files the module needs, and adapt the manifest from the nearest live
module. Add callbacks, utilities, repositories, middleware, or services only when the defined boundary requires them.

## Validation

- Import the module package.
- Verify `LoadedModule.from_module(...)` accepts its manifest.
- Verify loader position, router inclusion, and handler registration.
- Verify commands, arguments, flags, callbacks, owner checks, and FSM states in scope.
- Verify repository, cache, external-service, hook, stats, and export contracts in scope.
- Update and compile catalogs.
- Run focused Ruff checks and Pyright.
