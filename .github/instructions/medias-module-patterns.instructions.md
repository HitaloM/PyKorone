---
name: medias-module-patterns
description: "Use when creating or editing the medias module in src/korone/modules/medias. Follow project structure and patterns for handlers, filters, provider adapters, platform packages, caching, and error reporting to keep new handlers/platforms maintainable."
applyTo: "src/korone/modules/medias/**/*.py"
---

# Medias Module Patterns for PyKorone

Use this guide for all changes under `src/korone/modules/medias/`.

## Goals

- Keep new media integrations consistent with existing handler and provider architecture.
- Prefer composable platform adapters (constants, parser, client, provider) over monolithic handlers.
- Keep failures soft (`None` return) and observable (structured logs and media error reporting).

## Directory and Layering

Follow this structure for new platforms:

- `handlers/<platform>.py`: thin handler class, usually no custom logic
- `utils/platforms/<platform>/constants.py`: regex patterns and API endpoints
- `utils/platforms/<platform>/parser.py`: pure extraction and normalization helpers
- `utils/platforms/<platform>/client.py`: network calls and payload decoding
- `utils/platforms/<platform>/provider.py`: orchestration and `MediaPost` assembly
- `utils/platforms/<platform>/types.py`: optional typed platform data models

Keep cross-platform logic in shared files only:

- `handlers/base.py`
- `filters.py`
- `utils/parsing.py`
- `utils/provider_base.py`
- `utils/types.py`
- `utils/url.py`
- `utils/error_reporting.py`

## Module Wiring

When adding a new platform handler:

1. Export provider in `utils/platforms/__init__.py`.
2. Create `handlers/<platform>.py` as a minimal subclass of `BaseMediaHandler`.
3. Import the handler in `medias/__init__.py`.
4. Add the handler to `__handlers__` in `medias/__init__.py`.
5. Update user-facing module info text if supported platforms are listed.

## Handler Pattern

Platform handlers should be minimal:

- subclass `BaseMediaHandler`
- set `PROVIDER`
- set `DEFAULT_AUTHOR_NAME`
- set `DEFAULT_AUTHOR_HANDLE`

Do not duplicate send/caption/cache logic in per-platform handlers unless there is a clear platform-only requirement.

## Filter and Auto-Download Contract

- URL extraction must flow through `MediaUrlFilter`.
- Provider URL regex (`PROVIDER.pattern`) is the source of truth for detection.
- Keep URL normalization via `normalize_media_url(...)`.
- Respect chat-level auto-download toggle via settings/disabling repository.
- Keep `/url` command bypass behavior intact.

## Provider Contract

All providers must extend `MediaProvider` and define:

- `name`
- `website`
- `pattern`
- `fetch(url: str) -> MediaPost | None`

Provider behavior expectations:

- Return `None` for unsupported links, parse failures, and empty media results.
- Build `MediaPost` with non-empty `media` list.
- Use `download_media(...)` for media downloads and retry/caching behavior.
- Preserve cancellation semantics (`asyncio.CancelledError` should not be swallowed).

## Parser and Client Rules

Parser layer (`parser.py`):

- keep functions deterministic and side-effect free
- prefer explicit coercion/type guards for weak external payloads, ideally via shared helpers in `utils/parsing.py`
- avoid I/O and network calls

Client layer (`client.py`):

- use shared HTTP session (`HTTPClient.get_session()`)
- use provider defaults for timeout and headers unless platform requires overrides
- return `None` on non-200 or invalid payloads
- use structured logs for platform-specific network failures

Shared parsing helpers (`utils/parsing.py`):

- use `coerce_str(...)`, `coerce_int(...)`, `dict_or_empty(...)`, and `dict_list(...)` for weak external payloads
- use `ensure_url_scheme(...)` for simple scheme normalization when a provider needs it
- keep these helpers side-effect free and reusable across platform parsers

## Shared Types

Use shared media dataclasses from `utils/types.py`:

- `MediaSource`: pre-download source metadata
- `MediaItem`: downloadable or cached telegram media
- `MediaPost`: final content package for handler delivery

Use `MediaKind` to classify media and keep type-safe branching.

## Caching and URL Normalization

- Keep source URL normalization consistent with `normalize_media_url(...)`.
- Keep source-level cache keys stable through provider/base helpers.
- Keep post-level cache payloads serializable and backward-tolerant.
- Avoid creating new cache namespaces unless there is a clear cross-platform need.

## Error Reporting

Use `capture_media_exception(...)` for unexpected failures in provider/handler flow.

When calling it:

- include `stage`
- include `provider`
- include `source_url` when available
- include contextual extras that help reproducing issues

## Performance and Limits

- Respect Telegram media constraints already enforced in `BaseMediaHandler`.
- Keep media group handling compatible with current group limit and caption constraints.
- Reuse existing compression/fallback paths for photo delivery.
- Avoid blocking operations in handlers; move CPU-heavy transforms to thread offload when needed.

## Keep Existing Contracts Stable

Do not break these established contracts without explicit migration:

- `BaseMediaHandler.filters()` uses `GroupChatFilter` and `MediaUrlFilter(PROVIDER.pattern)`
- `MediaProvider.safe_fetch(...)` wraps provider fetch and standardizes failures
- module handler wiring through `medias/__init__.py` `__handlers__`

## Implementation Checklist for New Platform

- Add platform regex and endpoint constants.
- Implement parser helpers with defensive extraction.
- Implement client calls with shared session and timeout rules.
- Implement provider `fetch(...)` returning `MediaPost | None`.
- Build media list via `download_media(...)`.
- Add thin handler class and module wiring.
- Validate URL matching, media send path, and cache hit behavior.
- Verify failure paths log context and do not crash handler pipeline.
