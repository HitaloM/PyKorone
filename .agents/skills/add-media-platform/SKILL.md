---
name: add-media-platform
description: Add and register a new PyKorone media provider. Use for a new supported platform, not fixes to an existing provider.
---

# Add a Media Platform

Extend the composed media pipeline. Read the shared [media contract](../py-korone-development/references/medias.md),
`models.py`, `container.py`, and one current provider with similar transport needs under `src/korone/modules/medias/`.
Load the [runtime reference](../py-korone-development/references/runtime.md) only for HTTP, file, or subprocess changes.

## Provider boundary

Verify canonical/alternate URLs, redirects, response shapes, unavailable content, and media transports against upstream
sources and safe captured inputs. If upstream verification is unavailable, make that limitation explicit.

Create `providers/<platform>/` with the pieces it needs: protocol constants, a deterministic parser, an instantiable
client receiving `HttpClient`, and a provider receiving that client and `MediaDownloader`. Add platform-specific models
only when useful. Keep the provider structural (`MediaProvider`), with immutable `ProviderInfo` and
`fetch(url: str, *, workspace: Path) -> MediaPost | None`.

Pass the service-owned workspace through `DownloadOptions`. Use the shared downloader for ordering, size enforcement,
retries, and source file-ID reuse. A custom source loader is for HLS, separate audio, offload, or another concrete transport
exception; delegate ordinary sources to `download_source(...)`. Inject `FFmpegTranscoder` when needed, and reserve a
downloader slot if FFmpeg itself fetches upstream content. Keep disk outputs alive until delivery completes.

Return `None` for expected unavailable/private/removed/unsupported/empty content. A successful post contains media.
Propagate cancellation and let unexpected defects reach the service boundary.

Instantiate the provider once in the ordered tuple in `container.py`; order determines URL precedence. Reuse the shared
handler, cache, and delivery adapter. Update supported-platform help text and complete
[localization-workflow](../localization-workflow/SKILL.md).

## Validation

Use deterministic captured inputs for the supported URL variants, parser/media metadata, expected misses, and applicable
image/video/carousel cases. Exercise registration and only the changed transport contracts: retries, limits, cache reuse,
cancellation, or special loaders. Follow `AGENTS.md` for Ruff, Pyright, and the no-new-tests policy. Report any live
upstream behavior that remains unverified.
