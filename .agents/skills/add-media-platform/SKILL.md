---
name: add-media-platform
description: Add a new supported platform to src/korone/modules/medias. Use only when implementing and registering a new media provider, its URL detection, extraction, transport, and supported-platform localization. Do not use for fixes or refactors of existing platforms.
---

# Add a PyKorone Media Platform

Implement and register a complete media provider through the shared media pipeline. Preserve the project boundaries even
when the upstream API looks simple; the template is intentionally structured so transport, parsing, and orchestration do
not collapse into one module as the provider evolves.

## Workflow

1. Read [py-korone-development](../py-korone-development/SKILL.md), then read its Python, handlers, modules, and medias
   references completely.
2. Inspect at least two existing providers: one structurally simple and one with transport or media requirements closest
   to the new platform. Follow current code, not assumptions encoded in this template.
3. Verify the live upstream contract when network access is available: canonical, alternate, regional, mobile, embedded,
   and shortened URLs; redirects; response shapes; private, removed, unavailable, and rate-limited states.
4. Define the platform boundary before coding: supported post types, URL normalization, endpoints, required headers,
   timeouts, retry semantics, media metadata, downloads, fallbacks, and expected failure states.
5. Create a package under `utils/platforms/<platform>/` with these default boundaries:
   - `constants.py`: URL patterns, endpoints, timeouts, and immutable protocol constants.
   - `parser.py`: deterministic, network-free URL and payload parsing into shared media types.
   - `client.py`: upstream HTTP requests, response validation, and transport-specific logging.
   - `provider.py`: the `MediaProvider` orchestration contract and `MediaPost` assembly.
   - `types.py`: only when typed upstream payloads or platform-specific value objects materially improve correctness.
   - `__init__.py`: the provider's public export.
6. Keep the complete package structure by default. Merge boundaries only when the user explicitly requests a smaller
   implementation or an adjacent established provider demonstrates that the split would be artificial.
7. Use shared parsing helpers, media types, HTTP session, cache namespaces, download behavior, and structured logging.
   Do not create a second cache or session abstraction for one platform.
8. Use request-level `RetryPolicy` for buffered metadata or HTML only when attempts, statuses, backoff, jitter, timeout,
   redirects, and body-read behavior match the upstream contract. The shared `ClientSession` has no automatic global
   retry, and request middlewares replace session middlewares.
9. Preserve specialized download handling for streaming limits, truncated payload detection, HLS/FFmpeg, audio merging,
   provider-specific redirects, or offloading. Do not force binary downloads through a metadata retry helper.
10. Return `None` for expected unavailable, private, removed, unsupported, or empty content. Propagate cancellation and
    avoid converting programmer errors into ordinary provider misses.
11. Export the provider and add it once to the ordered `utils.platforms.PROVIDERS` registry. Registry order defines URL
    precedence and drives filtering, the shared `MediaHandler`, and the manifest. Do not create a platform handler.
12. Update supported-platform user text and use `localization-workflow` whenever visible strings or catalogs change.

## Template

Copy [assets/platform_template/platform](assets/platform_template/platform) to `utils/platforms/<platform>`. Rename every
example symbol and URL, then replace all placeholder payload assumptions with the verified upstream contract. The
template demonstrates the project's normal package boundaries, complete media metadata extraction, request-scoped retry,
shared downloads, expected-failure handling, and provider export.

Do not overwrite `utils/platforms/__init__.py`; export and register the provider manually. Do not retain placeholder
behavior, generic headers, or retry values without verifying the current external contract. Do not copy the template as
a substitute for inspecting analogous providers.

## Validation

- Canonical, alternate, mobile, regional, and shortened URLs.
- Invalid and unsupported URLs.
- Supported image, video, carousel, quote, and unavailable cases.
- Non-empty `MediaPost` only on success, stable normalized cache keys, and file-ID cache hits.
- Retry, timeout, cancellation, transient transport, and any special download behavior.
- Registry order, shared handler detection, and manifest loading.
- Catalog update and compilation when localization changes.
- Small deterministic reproductions using captured local inputs when useful; no check may depend on a live platform response.
- Do not create tests, test files, test fixtures, or introduce a test framework unless the user explicitly requests it.
- Focused Ruff and Pyright with zero new diagnostics.
