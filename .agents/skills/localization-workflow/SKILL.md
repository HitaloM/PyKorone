---
name: localization-workflow
description: Update PyKorone user-facing strings or gettext catalogs. Use when visible strings are added, changed, or removed under src/korone, or when files under locales are edited; manually review pt_BR translations, preserve placeholders, resolve fuzzy entries, and compile catalogs.
---

# Localization Workflow

Complete the catalog update, manual review, and compilation in the same change as the user-facing string.

## Workflow

1. Run `make update_lang`.
2. Review changed entries in `locales/pt_BR/LC_MESSAGES/korone.po` manually.
3. Keep `locales/en_US/LC_MESSAGES/korone.po` synchronized through the catalog update.
4. Translate every new or changed `msgid` in required locales.
5. Remove or resolve all affected `fuzzy` markers.
6. Run `make compile_lang`.
7. Inspect the final diff for unrelated catalog churn.

## Tooling

- Prefer Makefile targets over direct gettext commands.
- Use `make new_lang LANG=<locale>` to add one locale.
- Use `make new_locale` only when the user explicitly requests the destructive full locale reset.
- Treat direct gettext commands as read-only debugging unless the normal Makefile flow cannot express the task.
- Use the helpers from `korone.utils.i18n`: runtime gettext aliases for immediate text, lazy aliases for deferred metadata, and ngettext aliases for plurals.

## Manual Review Rules

- Preserve placeholders and syntax exactly: `{name}`, `%(name)s`, markup, and HTML entities.
- Preserve meaning, tone, and command intent.
- Review `msgid_plural` and every `msgstr[n]`.
- Manually review machine-generated translations before accepting them.
- Do not edit compiled `.mo` files.
- Avoid editing `.pot` files except when debugging extraction.

## Completion Checks

- Expect visible source changes to produce a corresponding `pt_BR` catalog change; explain explicitly when they do not.
- Confirm no placeholder mismatch between each source and translation.
- Confirm compilation succeeds.
- Keep translator comments, context, and unrelated catalog entries intact.
