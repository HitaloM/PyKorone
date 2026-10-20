---
name: review-aiogram-updates
description: Assess recent aiogram releases against PyKorone usage and recommend concrete adoption or migration work. Analysis only unless implementation is requested.
---

# Review aiogram Updates

Read the allowed range in `pyproject.toml` and resolved version in `uv.lock`. Use the requested comparison window;
otherwise review newer stable releases, or the latest stable release versus its predecessor if the lock is current.

Browse current primary sources: the official aiogram changelog/docs, `aiogram/aiogram` releases and relevant PRs, and
PyPI release metadata. Record versions, dates, and links, distinguishing stable releases from unreleased changes.

For each material API change, search actual PyKorone usage and trace its consumers. Consult the
[handler reference](../py-korone-development/references/handlers-aiogram.md) for commands, callbacks, middleware, and
aiogram typing; select other [development references](../py-korone-development/SKILL.md) only as needed for affected
UI, module loading, transport, or runtime behavior.

Recommend adoption when it fixes an exposed defect, removes a workaround, enables requested behavior, or reduces
demonstrable maintenance risk. Do not propose a feature merely because upstream added it. Do not edit dependencies,
code, or the lockfile for an analysis-only request. If implementation is requested, use the development workflow,
or `issue-fixer` for a demonstrated defect.

## Report

Include the allowed/resolved version, reviewed range and publication dates, and a compact comparison of material changes:
upstream source → affected local files/behavior → decision and reason → compatibility risk and confidence.

Use decisions such as **fix now**, **adopt now**, **prepare migration**, **investigate/measure**, or **no action**.
Prioritize concrete next steps, distinguish facts from inference, and state explicitly when nothing is actionable or
upstream verification was unavailable.
