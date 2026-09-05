# Handlers and aiogram

Use the active aiogram range in `pyproject.toml` and the current PyKorone implementations. Avoid legacy aiogram v2 patterns.

## Runtime and Routing

- Reuse the shared `bot`, `dp`, and dispatcher setup. FSM is currently disabled; do not assume `self.state` or FSM
  storage is available. A feature needing FSM must explicitly configure and validate that runtime contract.
- Do not instantiate feature-local `Bot` or `Dispatcher` objects.
- Compose routing through module manifests and the loader.
- Put module-specific middleware implementations in `src/korone/modules/<module>/middlewares/`; do not place
  middleware classes in handlers, utilities, or the module `__init__.py`.
- Export intentional middleware entry points from `middlewares/__init__.py` and register them in the module's
  `pre_setup()` hook declared through `ModuleManifest.scripts`.
- Keep polling, webhook, allowed-update resolution, and lifecycle logic centralized.
- Preserve middleware registration order and use outer middleware only when logic must wrap the complete update path.

## Handler Workflow

1. Read the nearest handlers, callbacks, manifest, filters, utilities, and repositories.
2. Choose `KoroneMessageHandler`, `KoroneCallbackQueryHandler`, `KoroneMessageCallbackQueryHandler`, or
   `KoroneInlineQueryHandler` for the incoming event. The error handler uses aiogram's error-specific base for `ErrorEvent`.
3. Define filters, project arguments, flags, callbacks, and FSM states declaratively.
4. Implement `filters()` and `async def handle(self)`.
5. Override `register(...)` only for dual-event or custom registration.
6. Register the class in `ModuleManifest.handlers`.
7. Keep business logic, external I/O, and database access outside `handle()` when reusable.

## Project Handler Context

- Use `self.event`, `self.bot`, `self.chat`, `self.context`, and `self.current_locale`.
- Use `self.answer(...)` for ordinary text/UI responses. It replies and falls back to a new message if the target
  disappeared. Message handlers return `Message`; dual-event responses may also return `bool` for edits. Use direct
  aiogram methods for uncovered transport (media, markup, inline results, alerts) and deliberate new-message sends.
  Keep domain-specific media fallbacks in their adapter.
- Use callback helpers such as `self.edit_text(...)` in callback handlers.
- Guard optional Telegram values such as `from_user`, callback messages, and inaccessible messages.
- Use `self.message` for an accessible callback/dual-event `Message`; use `check_for_message()` only when an early
  explicit guard is needed. Absent/inaccessible messages raise the project error. This guard does not authorize
  the callback owner. Do not repeat casts or silent guards after this validated boundary.
- Outside handlers, use `reply_message` / `reply_message_rich` and `edit_message_text` / `edit_message_rich` from
  `modules.utils_.reply_or_edit`. Replies
  recover missing targets; edits route ephemeral messages and propagate errors. Handler edit helpers suppress only
  unchanged-message errors; lower-level callers may interpret that error themselves.
- Use `BooleanStatusHandler` for BooleanArg-based on/off settings. Another status abstraction needs a concrete
  nonboolean parser and caller; do not cast BooleanArg output to an unconstrained generic type.
- `common_try` is only for best-effort Telegram operations whose caller accepts its ignored errors. Do not wrap
  an entire handler or persistence operation in generic retry/suppression.

## Arguments, Filters, and Flags

- Use argument types from `korone.args` instead of manually splitting commands with arguments.
- Define an immutable, slotted dataclass for parsed values, bind it with `ArgumentSchema(...)`, parameterize
  `KoroneMessageHandler` with that dataclass, and read values from `self.args`.
- If middleware also consumes parsed values, put the shared dataclass in the module's `args.py`, read
  `PARSED_ARGUMENTS_KEY`, and narrow to that type. Do not read legacy per-argument `data` keys or import the handler.
- Express optional arguments with dataclass defaults. Input that is present but invalid must remain an error; do not
  recreate the removed `OptionalArg` fallback behavior.
- Prefer core types such as `TextArg`, `WordArg`, `BooleanArg`, and `OrArg`; use module-local types such as
  `korone.modules.users.args.UserArg` for domain-specific parsing and resolution.
- Leave `arguments` unset for handlers without command arguments so `ArgumentsMiddleware` can take its fast path.
- Localize argument descriptions with `lazy_gettext as l_`.
- Use aiogram `Command`, `CommandStart`, `StateFilter`, and `F` with reusable filters from `korone.filters`.
- Return a tuple from `filters()`.
- Add `@flags.help(...)` to public commands and exclude internal, state-only, or callback-only routes.
- Add `@flags.disableable(...)` only when the command participates in chat-level disabling.
- Read handler flags in middleware with `aiogram.dispatcher.flags.get_flag(data, "name")`; do not reach through
  `data["handler"].flags` directly.
- Declare flags with aiogram's `@flags.<name>(...)` decorator or the registration `flags={...}` argument before the
  handler is registered. For programmatically derived flags, apply the decorator to the handler class before calling
  `register(...)`; do not mutate `HandlerObject.flags` after registration.
- Keep custom flag names public-style without a leading underscore because aiogram's `FlagGenerator` rejects private
  names. When subclasses can inherit a dynamic flag, explicitly apply a falsy value to ineligible subclasses so an
  inherited value cannot accidentally enable middleware behavior.

## Responses and Localization

- Wrap runtime text with `gettext as _` and deferred metadata with `lazy_gettext as l_`.
- Import text primitives and declarative factories from `korone.ui` for structured output.
- Pass `UI`, `UIExpression`, or aiogram `Text` values directly to `self.answer(...)`, `self.edit_text(...)`, and other
  project boundaries; do not call `str()`, render HTML, or set a parse mode.
- Use `template(...)` for translated strings containing formatted dynamic values, and use `link(...)` or `mention(...)`
  for semantic links.
- Import helpers from `korone.ui.rendering` only when implementing a low-level aiogram transport boundary that cannot
  use a project handler helper.
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
- Never pass a database primary key to Telegram API methods or retry Telegram-ID lookup as primary-key lookup.
- Share member permission evaluation through `check_member_permissions`; use `check_user_admin_permissions` for
  model/cache resolution and operator policy. Keep anonymous identity resolution in the filter.
- Match Telegram failures with `utils.telegram_errors`. Feature predicates use `normalized_error_message` and
  normalized phrases instead of independent casing or underscore rules.
- Localization fallback is limited to locale resolution. Never rerun a failed handler under another middleware.

## Validation

- Check handler registration, filters, flags, argument parsing, callbacks, authorization, and FSM transitions.
- Run focused Ruff checks and Pyright.
- Broaden validation for shared handler bases, middleware, repositories, or module loading.
