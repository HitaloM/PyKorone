---
name: localization-workflow
description: Update and manually review PyKorone gettext catalogs when user-facing strings or locales change, then compile them.
---

# Localization Workflow

Complete extraction, translation review, and compilation in the same change as visible text.

## Source text

Use helpers from `korone.utils.i18n`: `gettext as _` for runtime strings, `lazy_gettext as l_` for deferred metadata,
and the plural helpers for counted messages. Keep shared metadata deferred: project `LazyProxy` evaluates uncached in
the current locale. Do not translate it at import time or copy Babel private state. Locale metadata maps belong to each
`I18nNew` instance.

Use `korone.ui.template` for structured values in translated text. Its placeholders accept simple names only:
conversions, format specifications, attribute access, and indexing are unsupported. For UI/compiler changes, also read
the [UI contract](../py-korone-development/references/text-ui.md).

## Catalog update

1. Run `make update_lang`; it extracts into the sole template, `locales/korone.pot`, updates all catalogs, and removes
   obsolete entries.
2. Manually review new/changed translations in `locales/pt_BR/LC_MESSAGES/korone.po`. Keep the source catalog
   `locales/en_US/LC_MESSAGES/korone.po` synchronized with empty translations so gettext falls back to the English msgid.
   If adding a locale, use `make new_lang LANG=<locale>` and include it in review.
3. Preserve placeholders, plural forms, context, and active translator comments. Resolve affected `fuzzy` entries before
   compiling: `make compile_lang` uses `--use-fuzzy`, so compilation alone does not prove review.
4. Run `make compile_lang` and inspect the final diff for unrelated churn. Do not hand-edit `.mo` files or create extra
   POT templates. `make new_locale` destroys the catalog tree; use it only for an explicitly requested full reset.

If a refactor only moves unchanged strings, compare extracted message IDs and avoid catalog churn solely for changed
source locations. Compile and explain why translation edits were unnecessary.

## Validation

Compare source/translation placeholders and plural variants; confirm affected entries are translated, reviewed, and
not fuzzy, and obsolete entries were removed. Preserve any existing literal markup without introducing parse-mode
rendering into structured UI. When deferred translation/rendering changes, reuse the same proxy, argument help, or module
description in `en_US`, `pt_BR`, then `en_US`; confirm text changes with locale and nested entities survive.

Report compilation results and any strings that could not be reviewed. A successful compile does not detect all
placeholder mismatches or translation mistakes.
