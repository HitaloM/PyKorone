---
description: "Use when creating or editing Python code in Korone. Defines general standards for style, handler architecture, i18n, logging, repositories, and error handling."
name: "Korone Python Coding Style"
applyTo: "**/*.py"
---

# Korone Python Coding Style

- These rules are a strong preference for all `**/*.py` files. When there is a clear technical conflict, prioritize correctness and explain the deviation.
- Use `from __future__ import annotations` at the top of new Python files.
- Keep imports grouped as: stdlib, third-party, and local (no parent relative imports).
- Use explicit type hints for parameters and return values. Prefer `T | None` over `Optional[T]`.
- For imports used only in type hints, use `if TYPE_CHECKING:`.
- Prefer `type` aliases for complex structures, with clear names.

## Async And Logging

- In async code, prefer `async with` and `await` for all I/O operations.
- Use `logger = get_logger(__name__)` to obtain a logger.
- In async functions, use async logging (`await logger.ainfo(...)`, `await logger.awarning(...)`, etc.).
- Pass log context via kwargs (for example `user_id=...`, `chat_id=...`) instead of string interpolation.

## i18n And Messages

- User-visible strings must use i18n with `gettext as _` and `lazy_gettext as l_`.
- Use `l_()` for lazy metadata/decorators and `_()` for runtime user-facing messages.
- Avoid building translatable phrases via concatenation; use named placeholders.

## Handlers And Modules

- In module handlers, inherit from base classes in `utils.handlers` and implement `handle()`.
- Register handlers with `@classmethod register(cls, router: Router)` and define `filters()` where applicable.
- For message/callback responses, prefer base helpers (`self.answer(...)`, `self.edit_text(...)`) instead of duplicating manual branches.
- In new modules, keep metadata in `__init__.py` (`__module_name__`, `__module_description__`, `__handlers__`).

## Middlewares And Aiogram Flags

- Prefer configuring middleware behavior through aiogram flags on handlers/registrations instead of ad-hoc keys in event data.
- For middleware decisions based on handler metadata, read flags via `get_flag(data, "<flag_name>")`.
- Reuse established flag contracts (`help`, `disableable`, `args`) and avoid introducing new flag names when an existing one already fits.

## Database And Repositories

- Keep database access in the repository layer; avoid direct SQLAlchemy usage inside handlers.
- In async repositories, use `async with session_scope() as session`.
- For Telegram user IDs coming from `ChatModel`, use `chat.chat_id` (not `chat.id`) when the domain value is a Telegram user id.

## Errors And Robustness

- For expected business-rule errors with user-facing messages, prefer `KoroneError`.
- Avoid `except Exception` unless necessary. When needed, log enough context and follow lint rules.
- Do not perform broad refactors outside the request scope; prefer small, focused changes.

## Lint And Quality

- Write code compatible with Ruff settings in the project (`ruff.toml`, line-length 120, ANN/ASYNC/I/LOG rules).
- Use `# noqa: <RULE>` only with a real and local justification.
