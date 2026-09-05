# Medias Module

Apply these contracts to changes under `src/korone/modules/medias/`. For a completely new supported platform, use
`add-media-platform` as the primary workflow.

## Architecture and Runtime Flow

- Keep immutable domain values and the `MediaProvider` protocol in `models.py`.
- Assemble cache, semaphores, downloader, transform services, clients, provider instances, registry, and application
  service only in `container.py`.
- Keep URL detection in `MediaUrlFilter`, provider precedence in `ProviderRegistry`, and orchestration in `MediaService`.
- Keep `MediaHandler` as the Telegram error/telemetry boundary and `TelegramMediaDelivery` as the only Telegram media
  transport adapter.
- Preserve chat-level auto-download settings and the `/url` bypass behavior.
- Do not recreate a generic `utils/` package, provider inheritance, classmethod providers, or feature-local HTTP/cache
  singletons.

## Provider Contract

Every provider is an instance satisfying `MediaProvider`, exposes immutable `ProviderInfo`, and implements
`fetch(url: str) -> MediaPost | None`.

- Inject the platform client and shared `MediaDownloader` through the provider constructor.
- Add the instance to the ordered tuple built in `container.py`; do not create a platform-specific handler.
- Keep clients responsible for upstream requests and parsers deterministic, side-effect free, and network free.
- Return `None` for supported unavailable, removed, private, invalid, or empty content.
- Return a `MediaPost` with at least one `PreparedMedia` on success.
- Use `MediaDownloader.download(...)` with `DownloadOptions`. Pass a source-loader strategy only for HLS remuxing,
  separate audio, offload, or another transport-specific requirement.
- Propagate cancellation. `MediaService` isolates provider failures, converting timeouts to misses and logging other
  exceptions before returning a miss. Do not add provider-local broad catches or repeat those logs.

## HTTP, Downloads, and Transforms

- Inject the runtime-owned `korone.http.HttpClient`; access its started `session` property instead of creating sessions.
- Use request-level `RetryPolicy` for metadata or buffered payloads when it preserves the upstream's attempts, statuses,
  backoff, jitter, timeout, redirects, and body-read behavior.
- Keep bounded binary streaming retry in `MediaDownloader`; it owns size enforcement, truncated-body recovery, source
  file-ID reuse, ordering, and cancellation.
- Use `PhotoProcessor` for Telegram-safe photos and `FFmpegTranscoder` for subprocess output. The transcoder delegates
  timeout and child-process cleanup to `korone.utils.subprocess.run_process`. Provider-specific network
  transforms must also reserve a downloader slot when FFmpeg performs the upstream download itself.
- Reuse `DEFAULT_MEDIA_HEADERS` and `DEFAULT_MEDIA_TIMEOUT` unless the platform requires verified overrides.

## Models, Cache, and Delivery

- Use `MediaSource` before download, `PreparedMedia` for Telegram-ready media, `MediaPost` for a fetched post, and
  `DeliveryReceipt` for sent Telegram file IDs.
- Use the injected `MediaCache`. Keep its `media:v2:post` and `media:v2:source` key contracts, TTL, batch ordering,
  corruption-as-miss behavior, and Redis failure degradation stable.
- Preserve captions, quotes, album order/limits, file-ID reuse, invalid-cache recovery, photo fallback, Telegram flood
  control, missing-reply behavior, permissions handling, and send timeouts.
- Keep cache persistence in `MediaService`; delivery returns receipts and must not write Redis directly.
- Log recovery once at the owning layer with provider, source URL, stage, source index, and source kind where useful.

## Validation

- Verify registry order and URL detection, representative parser inputs, cache v2, source reuse, captions, quotes,
  single media, albums, retries, fallbacks, cancellation, transform limits, and shutdown behavior affected by the change.
- Import the manifest, run focused Ruff and full Pyright, and use captured local inputs or deterministic fakes.
- Do not create tests, test files, fixtures, or a test framework unless the user explicitly requests it.
