# Media pipeline

Use for existing code in `src/korone/modules/medias/`; a new platform uses
[add-media-platform](../../add-media-platform/SKILL.md) as its primary workflow.

## Ownership

| Responsibility | Source |
| --- | --- |
| Immutable domain values and structural `MediaProvider` protocol | `models.py` |
| Cache, semaphores, clients/providers, registry, service assembly | `container.py` |
| Detection and ordered provider precedence | `filters.py`, `registry.py` |
| Cache lookup, post workspace/concurrency, fetch/send/cache orchestration | `service.py` |
| Telegram error/telemetry boundary and transport adapter | `handlers/media.py`, `delivery.py` |
| Bounded downloads and transforms | `download.py`, `transforms/` |

Preserve auto-download settings and the `/url` bypass. Do not add platform-specific handlers, provider inheritance,
classmethod providers, or parallel HTTP/cache singletons.

## Provider and data flow

Providers are instances with immutable `ProviderInfo` and `fetch(url: str, *, workspace: Path) -> MediaPost | None`.
Inject their client and the shared downloader. Clients own upstream requests; parsers are deterministic and network-free.
Return `None` for expected private/removed/invalid/empty content and a nonempty post on success. Cancellation propagates;
`MediaService._safe_fetch` converts timeouts and unexpected provider failures to misses with logging at that boundary.

Use `MediaSource` before downloading, `PreparedMedia` for Telegram-ready files, `MediaPost` for the post, and
`DeliveryReceipt` for sent file IDs. Delivery returns receipts; only the service persists them to the media cache.

## Download and file lifetime

Use `MediaDownloader.download(...)` / `DownloadOptions`. A source-loader strategy handles HLS, separate audio, offload,
or another transport exception and delegates ordinary sources to `download_source(...)`. Preserve streaming retries,
truncated-body cleanup, size checks, source file-ID reuse, and source order. Metadata may use HTTP `RetryPolicy` when its
request semantics fit; streaming retry remains in the downloader.

`MediaService` owns a post workspace/concurrency slot through fetch, delivery, and cache persistence. Cache hits bypass
the active-post limit. Pass its workspace through download options, using separate source subdirectories. Videos stream
to disk in both Bot API modes; read current video/photo/thumbnail limits from `korone.constants` and downloader settings.

Keep disk output as `FSInputFile`; strings in `PreparedMedia.file` are cached Telegram file IDs. Resolve shared server paths
only in delivery, including albums. `FFmpegTranscoder` returns a validated nonempty path and uses the shared subprocess
runner; its child must exit or be reaped before workspace cleanup. It owns transform slots; FFmpeg upstream downloads
also reserve a downloader slot. `PhotoProcessor` owns Telegram-safe photo conversion.

Read [runtime.md](runtime.md) for shared HTTP, subprocess, and Telegram file ownership. Reuse default media headers and
timeouts unless the platform requires a verified override.

## Cache and recovery

Preserve `media:v2:post` / `media:v2:source` keys, TTLs, ordering, corruption-as-miss, and Redis failure degradation.
Keep captions, quotes, album ordering/limits, invalid-cache recovery, photo fallback, flood control, missing replies,
permissions handling, and send timeouts when changing their consumers. Log recovery once with useful provider/source/stage
context at its owning boundary rather than repeating broad provider catches.

## Validation

Use captured local inputs or deterministic fakes for changed parsing, detection/registry order, media metadata, cache
reuse, delivery, and transport paths. Include relevant limits, retries, cancellation, or cleanup when those contracts
change. Use controlled manifest imports and relevant Ruff/Pyright checks; follow `AGENTS.md`'s no-new-tests policy.
