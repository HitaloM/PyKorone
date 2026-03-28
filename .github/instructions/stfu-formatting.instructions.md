---
description: "Use when formatting user-facing Telegram text with stfu-tg in Korone handlers, module metadata, status messages, and error responses. Covers Doc/Template/Section composition and safe HTML output patterns."
name: "Korone stfu-tg Formatting"
---

# Korone stfu-tg Formatting

- These rules are strong preferences for composing Telegram messages with stfu-tg.
- Keep this instruction on-demand; do not add a broad `applyTo` unless explicitly requested.
- Prefer stfu-tg elements over handwritten HTML markup.

## Core Composition Rules

- Build rich message blocks with `Doc(...)` for multi-line or multi-part responses.
- Use `Template(...)` for translated strings with placeholders.
- Use semantic elements for formatting intent:
  - `Code(...)` for command names, IDs, and literal values.
  - `Url(...)` for links.
  - `UserLink(...)` for user mentions.
  - `Section(...)`, `KeyValue(...)`, and `Title(...)` for structured summaries.
- For incremental composition, start with `doc = Doc()` and append with `doc += ...`.

## i18n And Placeholders

- Keep user-visible text inside `_()` / `l_()` and inject dynamic values through stfu `Template(...)` placeholders.
- Avoid concatenating translated fragments when placeholders can express the full sentence.
- Prefer named placeholders (`{command}`, `{id}`, `{user}`) over positional formatting.

## Rendering And Sending

- Convert stfu elements to text only at the send/edit boundary (`str(doc)`, `str(template)`).
- Use `.to_html()` when an API expects an explicit HTML string or when helper functions return markup-oriented text.
- Do not mix raw HTML tags with stfu elements in the same message path unless strictly required.

## Handler Integration Patterns

- For handler responses, prefer base helpers and keep formatting local to response construction.
- Use `Element | str` compatible signatures in helper functions that can accept stfu elements.
- In module metadata (`__module_info__`), prefer `Doc(l_(...))` style lazy, translatable descriptions.

## Error And Status Messaging

- For user-facing errors, prefer structured stfu output (`Doc`, `Italic`, `KeyValue`, `Title`) rather than plain unformatted text.
- For command usage hints, combine `Template(...)` with `Code("/command")` consistently.
- Keep status progress messages concise and safe for edits (`edit_text(str(doc))`).

## Consistency And Safety

- Keep one semantic concern per element (content, emphasis, link, key-value), then compose in `Doc`.
- Reuse established element choices across modules to keep tone and formatting consistent.
- Avoid custom escaping utilities when stfu elements already provide safe formatting for the target output.
