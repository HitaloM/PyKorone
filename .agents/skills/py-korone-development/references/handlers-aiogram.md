# Handlers and aiogram

Use the active aiogram range in `pyproject.toml` and the current PyKorone implementations. Avoid legacy aiogram v2 patterns.

## Runtime and Routing

- Reuse the shared `bot`, `dp`, configured storage, and dispatcher setup.
- Do not instantiate feature-local `Bot` or `Dispatcher` objects.
- Compose routing through module manifests and the loader.
- Keep polling, webhook, allowed-update resolution, and lifecycle logic centralized.
- Preserve middleware registration order and use outer middleware only when logic must wrap the complete update path.

## Handler Workflow

1. Read the nearest handlers, callbacks, manifest, filters, utilities, and repositories.
2. Choose `KoroneMessageHandler`, `KoroneCallbackQueryHandler`, or `KoroneMessageCallbackQueryHandler` for the incoming event.
3. Define filters, ASS arguments, flags, callbacks, and FSM states declaratively.
4. Implement `filters()` and `async def handle(self)`.
5. Override `register(...)` only for dual-event or custom registration.
6. Register the class in `ModuleManifest.handlers`.
7. Keep business logic, external I/O, and database access outside `handle()` when reusable.

## Project Handler Context

- Use `self.event`, `self.bot`, `self.state`, `self.chat`, `self.context`, and `self.current_locale`.
- Use `self.event.reply(...)` in message handlers.
- Use callback helpers such as `self.edit_text(...)` in callback handlers.
- Use `self.answer(...)` only where the selected handler base defines it.
- Guard optional Telegram values such as `from_user`, callback messages, and inaccessible messages.
- Use `check_for_message()` and project exceptions where the nearby implementation does.

## Arguments, Filters, and Flags

- Use ASS types instead of manually splitting commands with arguments.
- Declare arguments in `handler_args(message, data) -> dict[str, ArgFabric]` and read parsed values from `self.data`.
- Prefer existing fabrics such as `TextArg`, `WordArg`, `BooleanArg`, `OptionalArg`, and `KoroneUserArg`.
- Localize argument descriptions with `lazy_gettext as l_`.
- Use aiogram `Command`, `CommandStart`, `StateFilter`, and `F` with reusable filters from `korone.filters`.
- Return a tuple from `filters()`.
- Add `@flags.help(...)` to public commands and exclude internal, state-only, or callback-only routes.
- Add `@flags.disableable(...)` only when the command participates in chat-level disabling.

## Responses and Localization

- Wrap runtime text with `gettext as _` and deferred metadata with `lazy_gettext as l_`.
- Use STFU elements such as `Doc`, `Title`, `Section`, `Template`, `Bold`, `Code`, `Url`, and `UserLink` for structured output.
- Pass dynamic values through `Template` or semantic elements instead of hand-built HTML.
- Use plain translated strings for simple messages.
- Run `localization-workflow` whenever visible text changes.

## Callback Data and FSM

- Define compact, typed `CallbackData` classes in the module's `callbacks.py` with unique stable prefixes.
- Pass callback instances to keyboard builders and filter with `YourCallback.filter(...)` and `F` when needed.
- Narrow `self.callback_data` before reading fields.
- Store an owner ID and authorize user-bound interactions.
- Answer callback queries promptly when feedback is required.
- Keep FSM states near the owning feature; transition and clear state deliberately.

## Middleware Data and IDs

- Pass middleware context through the shared `data` mapping.
- Use `KoroneContextData`, `self.context`, or helpers in `korone.middlewares.context_data` instead of scattered casts.
- Use `chat_id` and `user_id` for Telegram IDs.
- Distinguish `ChatModel.chat_id` from its database primary key `ChatModel.id`.
- Never pass a database primary key to Telegram API methods.

## Validation

- Check handler registration, filters, flags, argument parsing, callbacks, authorization, and FSM transitions.
- Run focused Ruff checks and Pyright.
- Broaden validation for shared handler bases, middleware, repositories, or module loading.
