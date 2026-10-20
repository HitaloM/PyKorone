# Handlers and aiogram

The source contracts live in `korone.utils.handlers`, `korone.args`, `korone.middlewares.context_data`, and
`modules.utils_.reply_or_edit`. Use the active aiogram range from project configuration.

## Entry points and context

Use `KoroneMessageHandler`, `KoroneCallbackQueryHandler`, `KoroneMessageCallbackQueryHandler`, or
`KoroneInlineQueryHandler`. The centralized error handler uses aiogram's error-specific base. Implement typed `filters()`
and `handle()` and register classes in `ModuleManifest.handlers`; override `register()` for dual/custom routing only.

Use `self.event`, `self.bot`, `self.chat`, `self.context`, and `self.current_locale`. Middleware passes shared data through
`KoroneContextData` / helpers in `middlewares.context_data`, rather than scattered casts. Trace middleware registration
and allowed updates in `korone.__main__` when changing shared context. FSM is disabled unless explicitly configured.

## Typed arguments and flags

- Define immutable slotted parsed-value dataclasses and bind them with `ArgumentSchema(...)` from `korone.args`.
  Parameterize `KoroneMessageHandler` and consume `self.args` instead of splitting command strings.
- If middleware also needs parsed values, place the shared dataclass in the module's `args.py` and narrow
  `data[PARSED_ARGUMENTS_KEY]` to it. Do not import handlers or read removed per-argument data keys.
- Dataclass defaults express absent optional input; present-but-invalid input remains an error. Leave `arguments` unset
  for commands without arguments so middleware can take its fast path.
- Use core `TextArg`, `WordArg`, `BooleanArg`, and `OrArg`; domain parsers belong to their module, such as `users.args.UserArg`.
  Localize descriptions with `lazy_gettext as l_`. Use `BooleanStatusHandler` for BooleanArg settings.
- Use aiogram commands/filters and reusable project filters. Public commands declare `@flags.help(...)`;
  `@flags.disableable(...)` opts into chat disabling. Internal/state/callback-only handlers do not need public help.
- Read flags with `aiogram.dispatcher.flags.get_flag(data, name)`. Declare decorators or registration flags before
  registration, never by mutating `HandlerObject.flags`. Custom flag names cannot start with `_`; explicitly clear
  inherited dynamic flags on ineligible subclasses.

## Responses and authorization

`self.answer(content)` on message handlers replies and recovers a missing reply target. Callback handlers use
`self.edit_text(...)` / `self.edit_rich(...)`; dual-event handlers expose `answer(...)` / `answer_rich(...)`.
Use direct aiogram methods for transports not covered by these helpers and deliberate new-message sends.

Outside handlers, use `reply_message` / `reply_message_rich` and `edit_message_text` / `edit_message_rich` from
`modules.utils_.reply_or_edit`. Edits route ephemeral messages; low-level edits propagate unchanged-message errors,
while callback/dual reply-or-edit helpers suppress only that error. Media fallback stays in its adapter.
`common_try` is for accepted best-effort Telegram failures, not blanket handler/persistence suppression.

Use `self.message` for a validated accessible callback/dual-event message. `check_for_message()` is an optional early
explicit guard, not an owner check. Use typed `CallbackData` in `callbacks.py` with stable unique prefixes, narrow the
payload, and authorize user-bound interactions separately. Guard genuinely optional Telegram fields and answer callback
queries when feedback is required.

Public admin helpers use Telegram IDs; use [persistence.md](persistence.md) for model keys. Share permission checks through
`check_member_permissions` and `check_user_admin_permissions`, with anonymous identity resolution in the filter.
Match Telegram errors through `utils.telegram_errors`; domain predicates reuse `normalized_error_message`.

## Middleware and content

Put module middleware in `middlewares/`, export entry points, and register in manifest `pre_setup()` hooks. Related
startup/shutdown observers belong there too. Preserve outer/inner middleware order; locale fallback only covers locale
resolution and must never catch and rerun a downstream handler. See [modules.md](modules.md) for hook concurrency.

Use plain translated strings for simple responses and public `korone.ui` factories for structured content. Pass UI or
aiogram `Text` directly to helpers. Read [text-ui.md](text-ui.md) for composition/rendering changes and use
[localization-workflow](../../localization-workflow/SKILL.md) when visible strings change.

## Validation

Check the affected registration, typed parsing, flags, context, authorization, and response behavior with deterministic
inputs. For shared middleware/handler changes include representative message, callback, inaccessible-message, and
ephemeral paths as applicable. Run relevant Ruff/Pyright checks and controlled import/dispatcher checks.
