---
name: issue-fixer
description: Diagnose and fix PyKorone bugs through evidence-driven root-cause analysis. Use for issue reports, exceptions, regressions, failing checks, incorrect Telegram behavior, broken module loading, middleware or handler context failures, database inconsistencies, cache problems, and unexpected external-provider responses.
---

# Issue Fixer

Fix the earliest verified divergence from the required contract. Treat the exception, failed assertion, or visible misbehavior as evidence, not automatically as the defect.

## Scope and Evidence

1. Read the complete report, traceback, logs, reproduction, and expected behavior.
2. Distinguish diagnosis-only requests from requests that authorize implementation.
3. Inspect `git status` and preserve unrelated changes.
4. Record uncertainty instead of turning an unverified theory into a patch.
5. Load `py-korone-development` and only the references matching the affected boundary.

## Root-Cause Workflow

1. State the observed behavior, expected behavior, trigger, and strongest evidence.
2. Reproduce with the smallest realistic input or command before editing.
3. Identify the failing value, transition, query, event, or contract at the symptom.
4. Trace backward through callers, middleware, repositories, parsers, caches, migrations, or external responses.
5. Find the first point where actual state diverges from the required contract.
6. Decide whether the value is required, optional, stale, malformed, or legitimately unavailable.
7. Fix the producer or contract at that point with the smallest coherent patch.
8. Add regression evidence that fails for the original behavior and succeeds after the fix.
9. Re-run the original reproduction and checks proportional to the changed boundary.

## Reject Symptom Masking

- Do not add broad `except`, `return`, `pass`, or default values merely to stop an exception.
- Do not replace required indexing with `.get(...)` until absence is a valid domain state.
- Do not scatter `None` guards when an upstream contract requires the value.
- Do not weaken annotations, add broad ignores, or cast away a data-flow defect.
- Do not retry deterministic parsing, validation, authorization, or schema failures.
- Do not change expected behavior to match the bug.

Use a fallback only when absence is valid by design. Represent it in the type and handle it at the earliest useful boundary.

## Boundary Checks

- Handlers: trace `self.data`, ASS arguments, flags, filters, middleware order, manifest registration, disabling, and allowed updates.
- Callbacks and FSM: verify typed payloads, owner checks, message accessibility, state transitions, and clearing.
- Database: inspect repository transaction scope, Telegram versus database IDs, migration state, and required backfills.
- Cache: inspect key construction, serialization, expiry, and invalidation.
- External services: capture safe status and response shape, validate adapter assumptions, and retry only transient failures.

## Regression and Completion

- Prefer a focused test or deterministic reproduction. Do not introduce a test framework for one issue unless requested.
- Catch only errors the layer can recover from or translate and preserve exception chaining.
- Log operational failures once with structured context; never log secrets or full sensitive payloads.
- Use `localization-workflow` if the fix changes visible text.
- Report the root cause, corrected contract, regression proof, commands and outcomes, and anything still unverified.
