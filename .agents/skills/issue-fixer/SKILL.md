---
name: issue-fixer
description: Diagnose PyKorone bugs, regressions, exceptions, and failing checks; implement a root-cause fix when requested.
---

# Issue Fixer

Find the earliest verified divergence from the required contract. A traceback or visible failure identifies a symptom;
it does not establish where the defect began. Respect diagnosis-only scope.

## Investigation and fix

- Establish the trigger, expected behavior, observed result, and evidence from the report and current code.
- Reproduce with the smallest realistic input. When services or captured responses are unavailable, state the limit and
  distinguish a verified local failure from an upstream hypothesis.
- Trace the failing value or transition through its producer and consumers. Read only the affected
  [development references](../py-korone-development/SKILL.md).
- Decide whether missing, stale, or malformed data is valid at that boundary. Correct the producer or contract with
  the smallest coherent patch; do not hide required values behind defaults, broad catches, casts, or silent returns.
- Demonstrate the regression with the same deterministic input before and after the change, following `AGENTS.md`'s
  no-new-tests policy. Re-run relevant static checks and the original reproduction when available.

Fallbacks belong where absence is valid and recoverable. Retry only transient failures, propagate cancellation, and log
recovery once at its owning layer. Use [localization-workflow](../localization-workflow/SKILL.md) for changed visible text.

## High-value traces

| Symptom | Follow the contract |
| --- | --- |
| Command ignored or wrong arguments | Manifest registration → filters/flags → `ArgumentsMiddleware` → typed `PARSED_ARGUMENTS_KEY` / `self.args`; absence and invalid input differ |
| Callback failure or wrong target | Typed payload → owner authorization → accessible `self.message` → response helper; message accessibility does not authorize the user |
| Missing database row or wrong admin | Owning repository → Telegram versus database ID → transaction/migration state; never retry the same number as another ID type |
| Wrong language or handler runs twice | Locale resolution → uncached proxy → rendering; fallback must not catch and rerun the downstream handler |
| Stale cache or shutdown failure | Shared key construction/invalidation → serialization/TTL → task ownership/cancellation → client closure |
| Provider failure | Safe response status/shape → deterministic parser → download/transport boundary; separate expected unavailability from programmer errors |

FSM is disabled in the default dispatcher. If the report involves state transitions, first verify that the runtime
actually enables storage. For shared middleware, check ordering and allowed-update resolution in `korone.__main__`.

Report the root cause, corrected contract, regression evidence, and anything still unverified. Do not present an
unreproduced external-service theory as a confirmed fix.
