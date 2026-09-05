---
name: add-media-platform
description: Add a new supported platform to src/korone/modules/medias. Use only when implementing and registering a new media provider, its URL detection, extraction, transport, and supported-platform localization. Do not use for fixes or refactors of existing platforms.
---

# Add a PyKorone Media Platform

Implement and register a provider through the composed media pipeline without creating platform-specific handlers,
sessions, caches, or download frameworks.

## Workflow

1. Read [py-korone-development](../py-korone-development/SKILL.md) and its Python, handlers, modules, medias, and
   text-UI references.
2. Inspect one simple provider and the existing provider closest to the new transport requirements.
3. Verify the upstream contract when network access is available: canonical and alternate URLs, redirects, response
   shapes, private/removed content, rate limits, headers, timeouts, media metadata, and fallbacks.
4. Create `providers/<platform>/` with only the boundaries the platform needs:
   - `constants.py` for URL patterns, endpoints, timeouts, and immutable protocol constants.
   - `parser.py` for deterministic, network-free parsing into shared media models.
   - `client.py` for an instantiable client receiving `HttpClient` in its constructor.
   - `provider.py` for an instantiable object satisfying `MediaProvider` and receiving its client plus
     `MediaDownloader`.
   - `models.py` only for useful platform-specific value objects.
   - `__init__.py` for intentional client/provider exports.
5. Expose immutable `ProviderInfo` with a unique stable key, display name, website, compiled URL pattern, and any caption
   options. Implement `fetch(url: str) -> MediaPost | None` without inheriting a base provider.
6. Use `MediaDownloader.download(...)` and `DownloadOptions`. Add a source-loader strategy only for HLS, separate audio,
   offload, or another real transport exception; delegate ordinary sources back to `download_source(...)`.
7. Inject `FFmpegTranscoder` only when required; it owns media slots and delegates process cleanup to `run_process`. If FFmpeg downloads the upstream itself, reserve a downloader slot for
   that operation.
8. Use request-level `RetryPolicy` only for metadata or buffered bodies whose retry contract is known. Binary streaming
   remains owned by `MediaDownloader`.
9. Return `None` for expected unavailable, private, removed, invalid, unsupported, or empty content. Propagate
   cancellation and let programmer errors reach `MediaService`.
10. Instantiate the client/provider in `container.py` and add the provider once to the ordered tuple. Registry order
    defines URL precedence.
11. Update the visible supported-platform text and run `localization-workflow` when that text changes.

## Validation

- Canonical, alternate, mobile, regional, embedded, and shortened URLs supported by the platform.
- Invalid URLs and private, removed, empty, rate-limited, image, video, carousel, and quote cases that apply.
- Non-empty `MediaPost` only on success; `PreparedMedia` metadata and source URLs remain correct.
- Metadata retry, streaming retry, timeout, cancellation, size limits, source cache hits, and special transports.
- Registry precedence, `MediaUrlFilter`, shared handler delivery, cache v2, and manifest loading.
- Catalog update/compilation when localization changes.
- Deterministic reproductions using captured inputs; do not depend on a live platform response.
- Do not add tests or a test framework unless the user explicitly requests them.
- Focused Ruff and full Pyright with zero diagnostics.
