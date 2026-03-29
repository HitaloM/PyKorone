---
name: localization-manual-translation
description: "Use when strings are added or changed in src/korone or when locale catalogs are edited. Enforce manual translation review and update workflow for language files."
applyTo: "{src/korone/**/*.py,locales/**/*.po,locales/*.pot,Makefile}"
---

# Manual Localization Workflow for PyKorone

## When This Applies

Apply this workflow whenever any user-facing string is added, changed, or removed.

Common triggers:

- New or changed text wrapped in translation helpers such as `_`, `l_`, `p_`, and `pl_`
- Edited command descriptions, help text, captions, errors, button labels, or docs shown to users
- Any direct edit under `locales/`

## Required Workflow

1. Refresh extraction and catalog updates:
   - `make update_lang`
2. Manually review changed entries in `locales/pt_BR/LC_MESSAGES/korone.po`.
3. Keep `locales/en_US/LC_MESSAGES/korone.po` synchronized through catalog updates; manual edits are optional.
4. Update translations for new and changed `msgid` entries in required locales.
5. Compile catalogs after manual review:
   - `make compile_lang`

## Gettext Tooling

- Prefer the repository `Makefile` targets over direct gettext commands when working on localization.
- Use `make update_lang` for extraction and catalog updates instead of calling `pybabel`, `msgmerge`, or related tools manually.
- Use `make compile_lang` to rebuild `.mo` files instead of running `msgfmt` directly.
- Use `make new_locale` or `make new_lang LANG=...` only when bootstrapping a locale from scratch.
- Treat `msgcat` as part of the extraction pipeline defined in the `Makefile`, not as a manual editing step.
- If a direct gettext command is needed for debugging, keep it read-only and do not bypass the normal translation review workflow.

## Manual Review Rules

- Keep placeholders and variable syntax identical between source and translation:
  - `{name}`
  - `%(name)s`
  - formatting markup and HTML entities
- Preserve meaning, tone, and command intent from source text.
- For pluralized messages, review all plural forms (`msgid_plural`, `msgstr[n]`).
- Resolve `fuzzy` entries created during updates in the same PR (hard rule).
- Machine translation is allowed.

## File Handling Rules

- Do not manually edit compiled files (`*.mo`).
- Avoid hand-editing template files (`*.pot`) unless debugging extraction behavior.
- Keep locale diffs minimal and focused on entries affected by the string change.

## Consistency Checks Before Finishing

- String changes in `src/korone/` should usually have corresponding `locales/pt_BR/LC_MESSAGES/korone.po` updates.
- If no translation update is needed, document the reason explicitly.
- Confirm no placeholder mismatch between `msgid` and translated `msgstr`.
- Confirm catalog compilation succeeds after review.

## Preferred PR Hygiene

- Group code string changes with related locale updates in the same change.
- Avoid unrelated bulk locale churn in the same PR.
- Keep translator-facing comments and context intact where present.
