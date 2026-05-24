---
name: korone-modules-plugin-contract
description: Use when creating or editing loadable top-level module packages under src/korone/modules, especially src/korone/modules/*/__init__.py files listed by korone.modules.MODULES. Follow the current ModuleManifest, ModulePackage, router, handlers tuple, scripts, stats, and export contract expected by the PyKorone runtime module loader.
---

# Module Package Contract for PyKorone

These rules define the runtime contract used by `korone.modules.load_modules` and `LoadedModule.from_module`.

## Required Export

Each loadable module package file, `src/korone/modules/<module>/__init__.py`, must expose one `manifest` object:

```python
manifest = ModuleManifest(
    package=ModulePackage(...),
    router=router,
    handlers=(HandlerA, HandlerB),
)
```

`LoadedModule.from_module(...)` raises if `manifest` is missing or is not a `ModuleManifest`.

Utility packages under `src/korone/modules/`, such as `utils_`, are exempt when they are not listed in `korone.modules.MODULES`.

## Router and Handlers

- Define `router = Router(name="...")` for modules that register handlers or middlewares.
- Pass that router through `ModuleManifest(router=router)`.
- Keep `handlers=(...)` as a tuple of handler classes, even for a single handler.
- Handlers listed in `manifest.handlers` should use project handler bases from `korone.utils.handlers`: `KoroneMessageHandler`, `KoroneCallbackQueryHandler`, and `KoroneMessageCallbackQueryHandler`.
- Handlers should follow the project registration pattern, using `filters()` and/or `register(...)` as required by the selected base class.

## Optional Exports

Represent optional behavior through `ModuleManifest` fields:

- `scripts=ModuleScripts(pre_setup=..., post_setup=...)`
- `stats=some_stats_provider`
- `export=ModuleExport(provider, private_only=True)`
- `package=ModulePackage(..., public=False)` for internal modules

## Package Metadata

Use `ModulePackage` for user-facing metadata:

- `name`
- `icon`
- `summary`
- `description`
- `public`

Prefer localized metadata values using `lazy_gettext as l_` and lazy descriptions with `LazyProxy`/`Doc` when the text is user-facing. Internal modules may use plain strings and `public=False`.

## Setup Hook Contract

- `pre_setup()` runs before module post-setup and receives no arguments.
- `post_setup(modules: ModuleRegistry)` runs after module loading and receives the loaded module mapping.
- Hooks may be sync or async. Sync hooks run through `asyncio.to_thread(...)`.

## Loader Compatibility Rules

- Do not use the old dunder module contract: `__module_name__`, `__module_emoji__`, `__module_description__`, `__handlers__`, `__pre_setup__`, or `__post_setup__`.
- Do not define a standalone `setup()` function in module package files.
- Use `ModuleRegistry` for type-only post-setup imports.
- Import callback classes with `as SameName` only when the module intentionally re-exports them for compatibility.

## Logging

- Use `from korone.logger import get_logger` and `logger = get_logger(__name__)` when logging is needed.

## Template

```python
from aiogram import Router
from stfu_tg import Doc

from korone.modules.metadata import ModuleManifest, ModulePackage
from korone.utils.i18n import LazyProxy
from korone.utils.i18n import lazy_gettext as l_

router = Router(name="module_name")

manifest = ModuleManifest(
    package=ModulePackage(
        name=l_("Module"),
        icon="?",
        summary=l_("Short module summary"),
        description=LazyProxy(lambda: Doc(l_("Longer user-facing description."))),
    ),
    router=router,
    handlers=(HandlerA, HandlerB),
)
```
