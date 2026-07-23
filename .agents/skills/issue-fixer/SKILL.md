---
name: issue-fixer
description: Diagnose and fix PyKorone bugs through evidence-driven root-cause analysis. Use when investigating or resolving issue reports, exceptions, regressions, failing checks, incorrect Telegram behavior, broken module loading, middleware or handler context failures, database inconsistencies, cache problems, or unexpected external-provider responses.
---

# Issue Fixer for PyKorone

Fix the earliest verified cause of the failure. Treat the exception, failed assertion, or visible misbehavior as evidence, not automatically as the defect itself.

## Required companion skills

- Load `.agents/skills/python-code-standards/SKILL.md` for Python diagnosis, implementation, or review.
- Load `.agents/skills/bot-handler-development/SKILL.md` and `.agents/skills/aiogram-project-patterns/SKILL.md` for handler, filter, callback, FSM, or middleware issues.
- Load `.agents/skills/korone-modules-plugin-contract/SKILL.md` for module discovery, manifests, registration, or lifecycle hooks.
- Load `.agents/skills/medias-module-patterns/SKILL.md` for failures under `src/korone/modules/medias/`.
- Load `.agents/skills/development-tooling/SKILL.md` for dependency, migration, runtime bootstrap, Docker, Ruff, Pyright, or workflow failures.
- Load `.agents/skills/localization-manual-translation/SKILL.md` when the fix changes user-facing text.

## Scope the request

- Read the full issue, traceback, logs, reproduction steps, and expected behavior when available. Do not infer the problem from the title alone.
- Distinguish diagnosis from implementation. For a diagnosis-only request, report the verified cause and supporting evidence without editing code.
- Inspect `git status` before editing and preserve unrelated user changes.
- Record uncertainties explicitly. Do not convert an unverified theory into a code change.

## Root-cause workflow

1. State the observed behavior, expected behavior, triggering conditions, and strongest available evidence.
2. Reproduce the failure with the smallest realistic input or command. Capture the exact failure before changing code.
3. Identify the failing value, state transition, query result, event, or contract at the symptom site.
4. Trace it backward through callers, constructors, middleware, repositories, parsers, caches, migrations, or external responses.
5. Find the first point where actual state diverges from the required contract.
6. Decide whether the value is required, optional, stale, malformed, or unavailable by design.
7. Fix the producer or contract at that first divergence. Keep the patch minimal and avoid unrelated refactors.
8. Add regression evidence that fails for the original behavior and succeeds after the fix.
9. Re-run the original reproduction, focused checks, and broader checks proportional to the affected boundary.

## Reject symptom masking

- Do not add a broad `except`, `return`, or `pass` merely to stop an exception.
- Do not replace required indexing with `.get(..., default)` until the value is proven optional.
- Do not scatter `if value is None` guards when the upstream contract requires a value.
- Do not weaken annotations, add ignores, or cast away a mismatch instead of fixing the data flow.
- Do not retry deterministic parsing, validation, authorization, or schema failures.
- Do not change expected behavior to match the current bug.

Use a fallback only when absence is a valid domain state. Represent that state in the type, handle it at the earliest useful boundary, and make the resulting behavior explicit.

## Trace PyKorone failure paths

### Handlers and middleware

- Trace `self.data` values to the middleware or ASS provider responsible for creating them.
- Check `KoroneContextData`, `as_korone_context(...)`, handler flags, and middleware order in `configure_dispatcher()`.
- For missing command arguments, inspect `handler_args(...)`, the automatic `args` flag, `ArgsMiddleware`, and the parsed key consumed by the handler.
- For handlers that never run, inspect filters, `manifest.handlers`, router inclusion, module selection, disabling flags, and resolved update types before changing handler logic.

### Callbacks and FSM

- Verify the typed `CallbackData` prefix and fields, keyboard construction, callback filter, owner checks, message accessibility, and callback age.
- Trace state creation, transition, filtering, and clearing. Do not clear FSM state early merely to hide a broken transition.
- Treat inaccessible messages and expired callbacks as genuine Telegram states only at boundaries where recovery is defined.

### Database and cache

- Keep SQLAlchemy access in repositories and inspect transaction scope, flush or commit timing, relationship keys, and migration state.
- Distinguish `ChatModel.chat_id` from `ChatModel.id`; confirm whether every value is a Telegram ID or database primary key.
- Check whether a schema change requires an Alembic migration and whether existing rows need a backfill.
- Verify Redis key construction, serialization, expiry, and invalidation before blaming stale consumers.
- Preserve exceptions across repository and domain boundaries when callers need to distinguish not-found, conflict, and infrastructure failures.

### External services

- Capture status, response shape, and the smallest safe payload needed to reproduce the parser or provider failure.
- Validate assumptions at the adapter boundary and translate specific transport or schema errors into domain errors.
- Retry only transient failures with bounded behavior. Do not retry malformed responses or deterministic rejections.
- Avoid logging secrets, authentication data, or full sensitive payloads.

## Exception and logging discipline

- Catch only exceptions the current layer can recover from or translate meaningfully.
- Preserve exception chaining with `raise DomainError(...) from exc` when introducing a domain boundary.
- Log an operational failure once at the layer with the best context, using `korone.logger.get_logger` and structured fields.
- Let unexpected exceptions reach centralized error handling instead of returning silent partial results.
- Give users a localized, actionable message only when the feature can degrade gracefully.

## Regression proof and validation

- Prefer a focused test or reproduction that fails before the fix and passes afterward.
- When an affected area has no test harness, create the smallest safe executable reproduction or deterministic check. Do not introduce an entire testing framework for one issue unless requested.
- Run `uv run ruff check <changed paths>` and `uv run pyright` for Python fixes.
- Run relevant localization, migration, module-loading, or runtime checks required by companion skills.
- Re-run the original failure path, not only adjacent happy paths.
- Report the root cause, changed contract, validation commands, outcomes, and any behavior that remains unverified.

## Completion checklist

- Reproduce or otherwise establish the failure path with evidence.
- Identify the first divergence, not only the crash line.
- Fix the producer, contract, or boundary responsible for the invalid state.
- Avoid silent fallbacks and broad exception swallowing.
- Preserve unrelated worktree changes.
- Add regression evidence and re-run the original scenario.
- Validate every affected shared boundary.
