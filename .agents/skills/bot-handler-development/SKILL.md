---
name: bot-handler-development
description: Develop and review PyKorone bot handlers using the project's aiogram 3 architecture. Use when creating or modifying handlers under src/korone/modules, handler filters and flags, ASS command arguments, STFU responses, typed callback data, FSM flows, Telegram and database ID handling, or handler registration in a module manifest.
---

# Bot Handler Development for PyKorone

Treat the current PyKorone code as authoritative. Use the project's ASS arguments, STFU output, paths, models, repositories, handler bases, middleware context, and module contracts.

## Required companion skills

- Load `.agents/skills/python-code-standards/SKILL.md` and `.agents/skills/aiogram-project-patterns/SKILL.md` for every Python handler change.
- Load `.agents/skills/korone-modules-plugin-contract/SKILL.md` when changing `src/korone/modules/<module>/__init__.py` or manifest wiring.
- Load `.agents/skills/localization-manual-translation/SKILL.md` whenever user-facing text changes.
- Load `.agents/skills/medias-module-patterns/SKILL.md` for work under `src/korone/modules/medias/`.

## Workflow

1. Read the nearest handlers, callbacks, module manifest, utilities, repositories, and filters before designing the change.
2. Select the project handler base that matches the incoming event.
3. Define filters, ASS arguments, flags, callback payloads, and FSM states declaratively.
4. Keep orchestration in the handler and move reusable business logic, external I/O, and database access to focused utilities or repositories.
5. Register the handler class through the module's `ModuleManifest.handlers` tuple.
6. Update gettext catalogs when user-facing strings change.
7. Run focused Ruff checks and Pyright; broaden validation when changing shared bases, middleware, repositories, or module loading.

## Handler architecture

- Extend `KoroneMessageHandler` for messages, `KoroneCallbackQueryHandler` for callbacks, or `KoroneMessageCallbackQueryHandler` only when one class genuinely handles both event types.
- Implement `filters()` and `async def handle(self)`. Override `register(...)` only for dual-event or custom registration.
- Use `self.event`, `self.bot`, `self.state`, `self.chat`, `self.context`, and `self.current_locale` instead of rebuilding middleware or aiogram plumbing.
- Reply through `self.event.reply(...)` in message handlers. Use `self.edit_text(...)` in callback handlers and `self.answer(...)` only in the hybrid message/callback base where that helper is defined.
- Guard optional Telegram data such as `from_user`, callback messages, and inaccessible messages. Use `check_for_message()` and project exceptions where appropriate.
- Do not instantiate feature-local `Bot` or `Dispatcher` objects. Create a module router only in the package manifest and register handlers through `manifest.handlers`.
- Keep every new or edited function fully annotated and keep imports explicit.

## ASS command arguments

- Use ASS types instead of manually splitting command text when the command has arguments.
- Declare arguments in `handler_args(message, data)` and return `dict[str, ArgFabric]`. Read parsed values from `self.data` in `handle()`.
- Prefer existing fabrics such as `TextArg`, `WordArg`, `BooleanArg`, `OptionalArg`, and project types such as `KoroneUserArg`.
- Localize argument descriptions with `lazy_gettext as l_`; the same metadata feeds parsing errors and generated help.
- Add a custom argument fabric under `src/korone/args/` only when existing compositions cannot express the grammar.
- Parse raw message text directly only for flows outside ASS's command-argument role, such as state replies or a deliberately free-form protocol.

```python
@classmethod
async def handler_args(
    cls,
    message: Message | None,
    data: dict[str, Any],
) -> dict[str, ArgFabric]:
    return {"query": TextArg(l_("Query"))}
```

## Filters, flags, and help

- Use aiogram filters such as `Command`, `CommandStart`, `StateFilter`, and `F` together with reusable filters from `korone.filters`.
- Return a tuple from `filters()`, including the trailing comma for one filter.
- Add `@flags.help(description=l_(...))` to public commands. Use help examples for non-obvious syntax and `exclude=True` for internal, state-only, or callback-driven routes.
- Add `@flags.disableable(name="...")` only when the command should participate in chat-level disabling. Let `DisablingMiddleware` enforce it; do not duplicate inline enablement checks.
- Use other established flags, such as `chat_action`, when they describe cross-cutting handler behavior.

## STFU responses and localization

- Wrap runtime user-facing text with `gettext as _` and deferred metadata with `lazy_gettext as l_`.
- Compose structured or interpolated output with STFU components such as `Doc`, `Title`, `Section`, `Template`, `Bold`, `Italic`, `Code`, `KeyValue`, `Url`, and `UserLink`.
- Pass dynamic values through `Template` instead of `.format()` or hand-built HTML. Use semantic STFU elements for user-provided values so escaping remains correct.
- Pass an `Element` directly to project helpers that accept it. Use `str(doc)` or `.to_html()` when an aiogram method requires a string, following the nearest working pattern.
- Keep plain `_()` strings for simple messages that need no formatting.
- Complete the manual gettext update, review, and compilation workflow in the localization skill whenever visible text changes.

## Callback data and FSM

- Define compact `CallbackData` subclasses in the module's `callbacks.py` with a unique, stable prefix and typed fields.
- Pass callback instances to keyboard builders and filter with `YourCallback.filter(...)`, optionally combined with `F`.
- Narrow `self.callback_data` to the expected callback type before reading fields.
- Authorize user-bound buttons by storing the owner ID in callback data and comparing it with `self.event.from_user.id`.
- Answer callback queries promptly when the interaction needs feedback. Handle expired or inaccessible callbacks only where the feature requires graceful recovery.
- Keep FSM states near the owning feature, clear stale state deliberately, and use `StateFilter` for state-specific handlers.

## Telegram IDs and database IDs

- Use `chat_id` or `user_id` for Telegram IDs. In `ChatModel`, `chat_id` is the Telegram ID and `id` is the SQLAlchemy primary key.
- Use names such as `chat_model`, `chat_model_id`, and `user_model_id` when working with database rows or foreign keys.
- Use `self.chat.chat_id` for the current Telegram chat and `self.chat.db_model` for its database model when middleware context is available.
- Read typed middleware values through `self.context` or helpers in `korone.middlewares.context_data`; do not scatter untyped casts across handlers.
- Put SQLAlchemy queries and transactions in repository classes. Call repositories asynchronously from handlers instead of opening sessions or joining models inline.
- Never pass `ChatModel.id` to Telegram API methods or compare it with Telegram user IDs; use `ChatModel.chat_id`.

## Errors, logging, and validation

- Catch only expected domain, network, or Telegram exceptions that the handler can translate into a useful result. Let unexpected failures reach the centralized error handling.
- Log recoverable operational failures with `korone.logger.get_logger` and structured context; never log secrets or full sensitive payloads.
- Keep pure formatting, parsing, and decision logic outside `handle()` when extracting it makes focused validation possible.
- Run `uv run ruff check <changed paths>` and `uv run pyright` for handler changes. If the repository gains relevant tests, add or update focused coverage for changed behavior and run it.
