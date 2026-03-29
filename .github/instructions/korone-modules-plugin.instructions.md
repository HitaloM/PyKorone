---
name: korone-modules-plugin-contract
description: "Use when creating or editing top-level module packages under src/korone/modules. Follow router, metadata, handler tuple, and setup hooks expected by the runtime module loader."
applyTo: "src/korone/modules/*/__init__.py"
---

# Module Package Contract for PyKorone

These rules define the runtime contract used by `korone.modules.load_modules` for top-level module packages.

## Required Exports

Each top-level module package file (`src/korone/modules/<module>/__init__.py`) should define:

- `router = Router(name="...")`
- `__module_name__`
- `__module_emoji__`
- `__module_description__`
- `__handlers__` as a tuple of handler classes

## Optional Exports

Define these only when needed:

- `__module_info__` for richer help/documentation metadata
- `__stats__` for module statistics integration
- `__pre_setup__()` hook
- `__post_setup__(modules: dict[str, ModuleType])` hook (sync or async)

## Handler Contract

Handlers listed in `__handlers__` should use the project handler bases from `korone.utils.handlers`:

- `KoroneMessageHandler`
- `KoroneCallbackQueryHandler`
- `KoroneMessageCallbackQueryHandler`

Handlers should follow the project registration pattern (`filters()` and/or `register(...)` as required by the selected base class).

## Loader Compatibility Rules

- Do not define a `setup()` function in module package files.
- Keep `__handlers__` as a tuple, even for a single handler.
- Keep metadata names as `__module_*__` (double underscore), not `MODULE_*`.
- Use `TYPE_CHECKING` guards for type-only imports like `ModuleType`.

## Localization and Logging

- Prefer localized metadata values using `lazy_gettext as l_` when user-facing.
- Use `from korone.logger import get_logger` and `logger = get_logger(__name__)` when logging is needed.

## Template

```python
from typing import TYPE_CHECKING

from aiogram import Router

from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from types import ModuleType

router = Router(name="module_name")

__module_name__ = l_("Module")
__module_emoji__ = "?"
__module_description__ = l_("Describe what this module does")

__handlers__ = (HandlerA, HandlerB)


def __pre_setup__() -> None:
    """Optional hook executed before post-setup stage."""


async def __post_setup__(modules: dict[str, ModuleType]) -> None:
    """Optional hook executed after module loading."""
```
