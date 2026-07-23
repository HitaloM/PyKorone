---
name: aiogram-project-patterns
description: Use when editing code that uses aiogram in src/korone. Enforce current aiogram 3.x APIs and PyKorone patterns for Dispatcher setup, routers, class-based handlers, middlewares, callback data, filters, and webhook or polling bootstrapping.
---

# Aiogram 3.x Usage for PyKorone

## Scope

- Apply these rules only when a change touches aiogram usage.
- Keep compatibility with the project dependency range in `pyproject.toml`: aiogram >=3.29.
- Prefer current aiogram 3.x APIs and avoid legacy v2-style patterns.

## Runtime Entry Points

- Use shared runtime objects from `korone`: `bot`, `dp`, and configured storage.
- Do not instantiate extra `Dispatcher` or `Bot` instances inside feature modules.
- Resolve allowed updates through `resolve_allowed_updates()`, which combines `dp.resolve_used_update_types()` with update types required by outer middleware.

## Polling and Webhook Bootstrap

- Polling mode should clear webhook state before startup with `await bot.delete_webhook(drop_pending_updates=True)`, then `await dp.start_polling(...)`.
- Webhook mode should use aiogram aiohttp integration with `SimpleRequestHandler`, `setup_application(...)`, and `bot.set_webhook(..., secret_token=..., allowed_updates=...)`.
- Keep lifecycle logic centralized in startup and shutdown functions.

## Router Composition

- Compose routing through module routers and loader flow, not ad hoc dispatcher wiring in random files.
- For top-level module packages in `src/korone/modules/*/__init__.py`, also follow `.agents/skills/korone-modules-plugin-contract/SKILL.md`.

## Handler Architecture

- Follow `.agents/skills/bot-handler-development/SKILL.md` for command arguments, responses, flags, callbacks, FSM flows, and handler data access.
- Prefer class-based handlers built on project bases from `korone.utils.handlers`: `KoroneMessageHandler`, `KoroneCallbackQueryHandler`, and `KoroneMessageCallbackQueryHandler`.
- Default pattern: implement `filters()` for message or callback handlers and implement `handle(self)` for execution.
- Override `register(...)` only when a handler must register both message and callback routes or custom wiring.
- Use `self.event.reply(...)` for `KoroneMessageHandler`, callback helpers such as `self.edit_text(...)` for `KoroneCallbackQueryHandler`, and `self.answer(...)` only on `KoroneMessageCallbackQueryHandler`.
- Let handlers register onto the module manifest router through their `register(...)` method; do not create module-local routers inside handler files unless that router is explicitly included by a manifest.

## Flags and Handler Metadata

- Use aiogram flags where appropriate for cross-cutting behavior and discoverability.
- Follow existing project conventions such as help or disableable flags used by middlewares and module help extraction.

## Filters

- Prefer project filters from `korone.filters` for chat and user constraints.
- Use aiogram built-in filters such as `Command`, `CommandStart`, and `F` when they improve readability.
- Keep filter logic reusable by moving repeated checks into filter classes.

## Callback Data

- Use typed callback payloads with `CallbackData` subclasses and explicit prefixes.
- Keep callback fields typed and minimal.
- Prefer passing `CallbackData` instances directly to keyboard builder buttons.
- Filter callback handlers with `YourCallback.filter(...)` and `F` expressions when matching on fields.

## Middlewares

- Middlewares should subclass `BaseMiddleware`.
- Pass computed context through the shared `data` dict so handlers and filters can consume it.
- Prefer the shared typed context helper in `src/korone/middlewares/context_data.py` when reading or writing middleware payload fields.
- Avoid ad hoc `dict[str, Any]` casts at middleware or handler boundaries when the context shape is known.
- Register middlewares in one central place and preserve established order.
- Use outer middleware only when logic must wrap full update processing.

## FSM and State

- Use `FSMContext` via project handler abstractions where available.
- Keep state transitions close to the handlers that own the conversation flow.
- Avoid creating alternate state storage paths outside configured dispatcher storage.

## Avoid These Patterns

- aiogram v2 APIs such as `executor.start_polling(...)`, decorator aliases from v2 migration examples, or `skip_updates=True` in polling startup.
- New feature code with raw callback data strings when typed `CallbackData` is appropriate.
- Mixing function-based and class-based handler styles in the same module without a clear reason.

## Minimal Examples

```python
from aiogram.filters.callback_data import CallbackData

class ItemAction(CallbackData, prefix="item"):
    action: str
    item_id: int
```

```python
from typing import TYPE_CHECKING

from aiogram.filters import CommandStart

from korone.filters.chat_status import PrivateChatFilter
from korone.utils.handlers import KoroneMessageHandler
from korone.utils.i18n import gettext as _

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType


class StartHandler(KoroneMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return CommandStart(), PrivateChatFilter()

    async def handle(self) -> None:
        await self.event.reply(_("Welcome"))
```
