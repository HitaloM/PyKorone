# Korone Text UI

Use this reference for changes to `src/korone/ui`, structured module output, lazy module descriptions, and low-level
message or caption rendering.

## Public Composition Contract

- Import public types, aiogram primitives, and factories from `korone.ui`.
- Use lowercase Korone factories: `column`, `row`, `field`, `section`, `bullets`, `numbered`, `template`, `link`, and
  `mention`. Do not import internal expression dataclasses or recreate an uppercase factory alias.
- Compose expressions declaratively and keep them immutable. Child collections may use `None` for conditional output.
- aiogram primitives may wrap Korone expressions, for example `Italic(template(...))` or `link(Bold(...), target)`;
  the compiler must preserve that recursive composition.
- Use only simple named placeholders in `template(...)`. Preserve placeholders across translations; conversions,
  format specifications, attribute access, and indexing are unsupported.

Plain `.format()` remains appropriate for plain strings needing numeric formatting; it must not flatten structured
values. UI templates retain their stricter simple-placeholder contract.

## Rendering Boundaries

- The only normal rendering path is `UIExpression -> aiogram.utils.formatting.Text -> text/entities`.
- Pass UI or `Text` directly to project handler helpers. Do not use `str(ui)`, HTML/Markdown rendering, escaping, or
  `ParseMode`.
- Keep `korone.ui`'s top-level exports limited to composition. Import `text_kwargs`, `caption_kwargs`,
  `message_text_kwargs`, `as_text`, or `plain_text` from `korone.ui.rendering` only in transport/integration code.
- Pass additional Telegram arguments naturally, such as
  `text_kwargs(content, disable_web_page_preview=True)`. Do not add mapping-based `merge_*` helpers.
- Use `plain_text(...)` only for Telegram surfaces that cannot carry entities, such as button labels, callback alerts,
  exception strings, or rich-message fields with their own formatting model.

## Compiler Invariants

- Compile `LazyProxy.value` recursively because a proxy may resolve to either a string or another UI expression.
  Project proxies are uncached by default; validate reuse across locales and do not copy Babel private attributes.
- Recursively compile Korone expressions nested inside any aiogram `Text` subclass; reject unsupported arbitrary
  objects instead of sending their `repr`.
- Avoid duplicate automatic `Bold` entities when a `field` label or `section` title is already a root `Bold` node.
- Indent every rendered line of each `section` child, including nested lists and styled multiline text.
- Preserve entities by transforming the `Text` tree through public iteration and `replace()` operations. Do not read
  `_body`, manipulate `MessageEntity` offsets, use private render flags, or rebuild an HTML/Markdown renderer.
- Keep template values immutable and fail immediately when a required placeholder is absent.

## Focused Validation

- Reproduce nested primitives (`Italic(template(...))` and links containing formatted expressions).
- Check Unicode text, repeated and escaped template placeholders, missing/invalid placeholders, and unsupported values.
- Verify that automatic bold produces one entity and multiline section children receive consistent indentation.
- Exercise text, caption, media-group, inline-message, and lazy module-description boundaries when affected.
- Search changed code for `str(ui)`, HTML renderers, parse modes, legacy formatting imports, uppercase link aliases, and
  private aiogram formatting internals.
- Run focused Ruff checks and Pyright. This repository has no automated test suite; use deterministic reproductions.
