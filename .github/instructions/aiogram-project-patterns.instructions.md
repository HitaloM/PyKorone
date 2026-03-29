---
name: aiogram-project-patterns
description: "Use when editing code that uses aiogram in src/korone. Enforce current aiogram 3.x APIs and project patterns for Dispatcher setup, routers, class-based handlers, middlewares, callback data, and webhook or polling bootstrapping."
applyTo: "src/korone/**/*.py"
---

# Aiogram 3.x Usage for PyKorone

## Scope

- Apply these rules only when a change touches aiogram usage.
- Keep compatibility with the project dependency range: aiogram >=3.26.
- Prefer the current aiogram 3.x APIs and avoid legacy v2-style patterns.

## Runtime Entry Points

- Use shared runtime objects from `korone`: `bot`, `dp`, and configured storage.
- Do not instantiate extra `Dispatcher` or `Bot` instances inside feature modules.
- Resolve allowed updates from handlers using `dp.resolve_used_update_types()`.

## Polling and Webhook Bootstrap

- Polling mode should clear webhook state before startup:
  - `await bot.delete_webhook(drop_pending_updates=True)`
  - then `await dp.start_polling(...)`
- Webhook mode should use aiogram aiohttp integration:
  - `SimpleRequestHandler`
  - `setup_application(...)`
  - `bot.set_webhook(..., secret_token=..., allowed_updates=...)`
- Keep lifecycle logic centralized in startup and shutdown functions.

## Router Composition

- Compose routing through module routers and loader flow, not ad hoc dispatcher wiring in random files.
- For top-level module packages in `src/korone/modules/*/__init__.py`, follow the dedicated module contract file:
  - `.github/instructions/korone-modules-plugin.instructions.md`

## Handler Architecture

- Prefer class-based handlers built on project bases from `korone.utils.handlers`:
  - `KoroneMessageHandler`
  - `KoroneCallbackQueryHandler`
  - `KoroneMessageCallbackQueryHandler`
- Default pattern:
  - implement `filters()` for message or callback handlers
  - implement `handle(self)` for execution
- Override `register(...)` only when a handler must register both message and callback routes or custom wiring.
- Prefer `self.answer(...)` and project helper methods over duplicating message or callback response plumbing.

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
- Register middlewares in one central place and preserve established order.
- Use outer middleware only when logic must wrap full update processing.

## FSM and State

- Use `FSMContext` via project handler abstractions where available.
- Keep state transitions close to the handlers that own the conversation flow.
- Avoid creating alternate state storage paths outside configured dispatcher storage.

## Avoid These Patterns

- aiogram v2 APIs such as:
  - `executor.start_polling(...)`
  - decorator aliases from v2 migration examples
  - `skip_updates=True` in polling startup
- New feature code with raw callback_data strings when typed `CallbackData` is appropriate.
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

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType


class StartHandler(KoroneMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return CommandStart(), PrivateChatFilter()

    async def handle(self) -> None:
        await self.answer("Welcome")
```
