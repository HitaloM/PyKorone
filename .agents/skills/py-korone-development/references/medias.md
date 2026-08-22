# Medias Module

Apply these contracts to changes under `src/korone/modules/medias/`. For a completely new supported platform, use
`add-media-platform` as the primary workflow.

## Runtime Flow

- Keep URL detection in `MediaUrlFilter` and the complete provider order in the single `utils.platforms.PROVIDERS`
  registry.
- Keep `MediaHandler` as the only platform-independent Telegram delivery handler.
- Keep the aiogram processing adapter in `middlewares/` and queue, concurrency, Redis lock, renewal, and shutdown
  behavior in `utils/processing.py`.
- Register middleware and lifecycle observers only from the module `pre_setup()` hook.
- Preserve chat-level auto-download settings and `/url` bypass behavior.

## Provider Contract

Every provider extends `MediaProvider` and defines `name`, `website`, `pattern`, and
`fetch(url: str) -> MediaPost | None`.

- Add the provider to `utils.platforms.PROVIDERS`; do not create a platform-specific handler.
- Return `None` for supported unavailable, removed, invalid, or empty content.
- Return a `MediaPost` with at least one downloaded `MediaItem` on success.
- Use shared `download_media(...)` behavior unless the platform requires HLS remuxing, separate audio, offload, or
  another transport-specific path.
- Propagate cancellation and let unexpected defects reach `safe_fetch(...)` or the shared download boundary.

For a new platform, follow the package boundaries and template defined by `add-media-platform`. During fixes and
refactors, preserve the existing provider shape unless the requested change makes a split or merge materially clearer.
Parser functions must remain side-effect free and network-free.

## HTTP and Downloads

- Use the shared session from `HTTPClient.get_session()`.
- Use `RetryPolicy` as request middleware for metadata or buffered payloads when it preserves the provider's attempts,
  status set, backoff, jitter, timeout, redirect, and body-read behavior.
- Do not install a media retry policy on the shared session; request-level policies differ by upstream.
- Keep bounded streaming retry in `MediaProvider` for binary media. It covers errors raised while reading the body,
  enforces the Telegram size limit before retaining an oversized payload, and distinguishes truncated payloads.
- Reuse provider defaults for headers and timeouts unless the upstream requires overrides.

## Types, Cache, and Delivery

- Use `MediaSource` before download, `MediaItem` for Telegram-ready media, `MediaPost` for delivery, and `MediaKind`
  for branching.
- Use `utils/cache.py` for the `media-post` and `media-source` namespaces. Keep serialized post payloads backward
  tolerant and source cache keys normalized and stable.
- Preserve captions, quotes, albums, file-ID reuse, invalid-cache recovery, photo compression, Telegram flood-control
  retry, missing-reply fallback, permissions handling, and Telegram limits in the shared handler.
- Log once at the layer that owns recovery, with provider, source URL, stage, source index, and source kind where useful.
- Run FFmpeg through asyncio's subprocess APIs. Offload measured CPU-bound Python work with an execution model that
  matches its GIL behavior; do not send it to `asyncio.to_thread()` by default.

## Validation

- Verify provider registry order, URL detection, representative parser inputs, post/source cache compatibility, captions, quotes,
  single media, albums, retries, fallbacks, cancellation, queue capacity, lock loss, and shutdown behavior affected by
  the change.
- Import the module manifest directly, run focused Ruff and Pyright, and exercise affected behavior with captured local
  inputs or a small deterministic reproduction. Do not create tests, test files, test fixtures, or introduce a test
  framework unless the user explicitly requests it.
