# Medias Module

Apply these contracts to changes under `src/korone/modules/medias/`. For a completely new supported platform, use `add-media-platform` as the primary workflow.

## Layers

- Keep `handlers/<platform>.py` thin.
- Keep URL and endpoint constants in `utils/platforms/<platform>/constants.py`.
- Keep deterministic extraction and normalization in `parser.py`.
- Keep network calls and payload decoding in `client.py`.
- Keep orchestration and `MediaPost` assembly in `provider.py`.
- Add `types.py` only when platform-specific models improve the boundary.
- Put cross-platform behavior only in shared handlers, filters, parsing, provider, settings, type, or URL modules.

## Handler and Detection Contracts

- Subclass `BaseMediaHandler` and normally set only `PROVIDER`, `DEFAULT_AUTHOR_NAME`, and `DEFAULT_AUTHOR_HANDLE`.
- Do not duplicate shared send, caption, cache, group, or compression behavior without a platform-only requirement.
- Flow URL extraction through `MediaUrlFilter`.
- Keep `PROVIDER.pattern` as the source of truth for detection.
- Normalize source URLs through `normalize_media_url(...)`.
- Preserve chat-level auto-download settings and `/url` bypass behavior.

## Provider Contract

Every provider must extend `MediaProvider` and define `name`, `website`, `pattern`, and `fetch(url: str) -> MediaPost | None`.

- Return `None` for unsupported links, unavailable or removed content, known parse failures, and empty media.
- Return `MediaPost` with a non-empty media list.
- Prefer shared `download_media(...)` retry and cache behavior.
- Preserve established platform-specific download paths only when required.
- Do not swallow `asyncio.CancelledError`.
- Let unexpected defects reach `MediaProvider.safe_fetch(...)` or the shared download boundary.

## Parser and Client Rules

- Keep parser functions side-effect free and network-free.
- Use explicit coercion and shared helpers such as `coerce_str`, `coerce_int`, `dict_or_empty`, and `dict_list`.
- Use `ensure_url_scheme(...)` for simple scheme normalization.
- Use the shared session from `HTTPClient.get_session()`.
- Apply provider defaults for headers and timeouts unless the platform requires overrides.
- Return `None` for expected non-success responses or invalid payloads.

## Shared Types and Cache

- Use `MediaSource` for pre-download data, `MediaItem` for Telegram-ready media, `MediaPost` for final delivery, and `MediaKind` for branching.
- Keep source cache keys stable.
- Keep post cache payloads serializable and backward-tolerant.
- Avoid new cache namespaces without a cross-platform requirement.

## Logging and Limits

- Log once at the layer with actionable context using structured fields such as `provider`, `source_url`, `stage`, `source_index`, and `source_kind`.
- Do not add manual Sentry capture.
- Respect Telegram size, group, and caption limits already enforced by `BaseMediaHandler`.
- Reuse photo compression and fallback paths.
- Offload CPU-heavy blocking work from the event loop.

## Stable Contracts

Do not change these without an explicit migration:

- `BaseMediaHandler.filters()` combines the group filter and `MediaUrlFilter(PROVIDER.pattern)`.
- `MediaProvider.safe_fetch(...)` standardizes provider failures.
- `medias/__init__.py` registers handler classes through `ModuleManifest.handlers`.
