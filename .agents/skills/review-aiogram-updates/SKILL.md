---
name: review-aiogram-updates
description: Analyze the latest or recent aiogram releases and upstream changes, map them to PyKorone's actual usage, and decide whether they can fix, improve, simplify, or add useful behavior. Use when the user asks what changed recently in aiogram, whether PyKorone should adopt new aiogram features or fixes, or for an aiogram upgrade impact review. Do not implement upgrades or code changes unless the user explicitly requests them.
---

# Review aiogram Updates

Produce an evidence-backed impact assessment of recent aiogram changes against the current PyKorone codebase.

## Review Workflow

1. Inspect `pyproject.toml` and `uv.lock` to identify the allowed range and exact resolved aiogram version.
2. Establish the comparison window:
   - use user-specified versions or dates when provided;
   - otherwise review every stable release newer than the resolved version;
   - if the resolved version is already current, review the latest stable release against its preceding stable release.
3. Browse current primary sources. Prefer the official aiogram changelog and documentation, GitHub releases and pull requests from `aiogram/aiogram`, and PyPI release metadata. Do not rely on model memory for current versions or changes.
4. Record release versions, dates, relevant links, deprecations, removals, migrations, fixes, and new APIs. Separate stable behavior from development-branch or unreleased changes.
5. Search PyKorone for each affected API or subsystem. Inspect the nearest implementation and the relevant
   [PyKorone development references](../py-korone-development/SKILL.md), especially
   [handlers and aiogram](../py-korone-development/references/handlers-aiogram.md).
6. Trace actual impact across handlers, filters, middleware, FSM, callbacks, polling or webhook startup, Bot API types, serialization, error handling, and typing only where the upstream change applies.
   Compare against [handler contracts](../py-korone-development/references/handlers-aiogram.md), including ephemeral-aware response helpers,
   uncached translations, disabled-by-default FSM, and the documented aiogram typing/inheritance boundaries.
7. Reject speculative adoption. A new upstream feature is relevant only when it removes a local workaround, improves a measured or evident weakness, enables requested behavior, or reduces maintenance risk.
8. Do not edit code, dependencies, or the lockfile during an analysis-only request. If implementation is requested, use `py-korone-development`; add `issue-fixer` when correcting a demonstrated defect.

## Decision Categories

Assign every relevant upstream change one outcome:

- **Fix now**: PyKorone is demonstrably exposed to a corrected upstream defect or incompatibility.
- **Adopt now**: the change provides a concrete benefit with acceptable migration risk.
- **Prepare migration**: a deprecation or breaking change requires planned work but not an immediate patch.
- **Investigate or measure**: value is plausible but local evidence is insufficient.
- **No action**: the change does not affect current usage or adds no meaningful benefit.

## Report Contract

Report:

- the installed constraint and resolved version;
- the reviewed release range and publication dates;
- each material upstream change with a primary-source link;
- affected local files and current behavior;
- decision, rationale, compatibility risk, and confidence;
- a prioritized next-action list.

State explicitly when no actionable change is found. Distinguish verified facts from inference and call out anything that could not be validated.
