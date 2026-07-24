---
name: add-media-platform
description: Add a new supported platform to src/korone/modules/medias. Use only when implementing a new platform provider, parser, client, handler, URL detection, exports, module wiring, and supported-platform localization. Do not use for fixes or refactors of existing platforms.
---

# Add a PyKorone Media Platform

Implement one complete platform adapter while preserving the shared media contracts.

## Workflow

1. Read [py-korone-development](../py-korone-development/SKILL.md) and its
   [Python](../py-korone-development/references/python.md),
   [handlers and aiogram](../py-korone-development/references/handlers-aiogram.md),
   [modules](../py-korone-development/references/modules.md), and
   [medias](../py-korone-development/references/medias.md) references.
2. Read two current platform implementations:
   - one structurally simple;
   - one with transport or media requirements similar to the new platform.
3. Verify canonical, alternate, regional, mobile, and shortened URL forms and the expected response formats.
4. Define the platform boundary before editing:
   - supported post types;
   - expected unavailable or private states;
   - required endpoints, redirects, headers, and timeouts;
   - image, video, carousel, and author metadata behavior.
5. Implement the platform package:
   - `constants.py`
   - `parser.py`
   - `client.py`
   - `provider.py`
   - `types.py` only when platform-specific models add value.
6. Keep parsing deterministic and network-free.
7. Use the shared HTTP session, media types, download helpers, cache behavior, and logged error boundaries.
8. Return `None` for supported domain failures such as unavailable, private, removed, unsupported, or empty content.
9. Preserve cancellation and let unexpected implementation defects reach the existing shared boundary.
10. Add a minimal `BaseMediaHandler` subclass.
11. Export the provider and register the handler in the medias manifest.
12. Update the supported-platform text and run `localization-workflow`.

## Scaffold Asset

Use [assets/platform_template](assets/platform_template) only as a structural starting point:

- copy `handler.py` to `handlers/<platform>.py`;
- copy `platform/` to `utils/platforms/<platform>/`;
- merge the new exports and handler registration into existing shared files manually.

Rename every `Example` symbol, replace every example URL and payload assumption, remove unused files, and do not leave placeholder behavior in the implementation. Never overwrite shared `__init__.py` or manifest files with template content.

Do not automate or copy platform semantics from the asset. The external service contract must come from verified current behavior.

## Validation

- Canonical, alternate, mobile, regional, and shortened URLs.
- Invalid and unsupported URLs.
- Image, video, carousel, and unavailable posts that the platform supports.
- Provider returns a non-empty `MediaPost` only on success.
- Cache hit behavior and stable normalized URLs.
- Cancellation and transient transport behavior.
- Handler and manifest registration.
- Catalog update and compilation.
- Focused Ruff checks and Pyright.
