---
name: localization-workflow
description: Update PyKorone user-facing strings or gettext catalogs. Use when visible strings are added, changed, or removed under src/korone, or when files under locales are edited; manually review pt_BR translations, preserve placeholders, resolve fuzzy entries, and compile catalogs.
---

# Localization Workflow

Complete the catalog update, manual review, and compilation in the same change as the user-facing string.

## Workflow

1. Run `make update_lang`.
2. Review changed entries in `locales/pt_BR/LC_MESSAGES/korone.po` manually.
3. Keep the source-locale catalog at `locales/en_US/LC_MESSAGES/korone.po` synchronized through the catalog update;
   leave its `msgstr` values empty so gettext falls back to the English `msgid`.
4. Translate every new or changed `msgid` in non-source locales, currently `pt_BR`.
5. Remove or resolve all affected `fuzzy` markers.
6. Run `make compile_lang`.
7. Inspect the final diff for unrelated catalog churn.

## Tooling

- Prefer Makefile targets over direct gettext commands.
- Treat `locales/korone.pot` as the only catalog template; do not recreate provider-specific or intermediate POT files.
- Expect `make update_lang` to remove obsolete entries from every PO catalog.
- Use `make new_lang LANG=<locale>` to add one locale.
- Use `make new_locale` only when the user explicitly requests the destructive full locale reset.
- Treat direct gettext commands as read-only debugging unless the normal Makefile flow cannot express the task.
- Use the helpers from `korone.utils.i18n`: runtime gettext aliases for immediate text, lazy aliases for deferred metadata, and ngettext aliases for plurals.
- Project `LazyProxy` defaults to uncached evaluation. Keep locale-dependent metadata uncached; never clone Babel
  private attributes or freeze a shared proxy in the first request's locale. Do not translate shared metadata at import.
- Locale metadata maps belong to each `I18nNew` instance, not shared mutable class state.
- For refactors that only move unchanged strings, compare extracted message IDs. Avoid catalog rewrites solely for
  shifted source references; compile catalogs and explain why no translation edit is required.

## Manual Review Rules

- Preserve placeholders and syntax exactly: `{name}`, `%(name)s`, markup, and HTML entities.
- For strings rendered with `korone.ui.template`, keep placeholders as simple names. Do not introduce conversions,
  format specifications, attribute access, or indexing in translations.
- Preserve meaning, tone, and command intent.
- Review `msgid_plural` and every `msgstr[n]`.
- Manually review machine-generated translations before accepting them.
- Do not edit compiled `.mo` files.
- Avoid editing `.pot` files except when debugging extraction.

## Completion Checks

- Expect visible source changes to produce a corresponding `pt_BR` catalog change; explain explicitly when they do not.
- Confirm no placeholder mismatch between each source and translation.
- Confirm no obsolete `#~` entries remain after updating catalogs.
- Confirm compilation succeeds. When deferred text/rendering changes, resolve the same proxy, argument help, and
  module description in `en_US`, `pt_BR`, then `en_US` again; verify nested entities survive.
- Keep active translator comments, context, and unrelated catalog entries intact.
