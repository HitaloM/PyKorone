# Runtime resources and transport

Use this reference for resource ownership, HTTP, caches, subprocesses, Telegram files, startup, and shutdown.
Deployment configuration and operations are covered by [tooling.md](tooling.md) and the deployment guide.

## Lifecycle

`src/korone/__init__.py` constructs settings, the Bot/API session, Redis, and a dispatcher with FSM disabled.
`src/korone/__main__.py` owns dispatcher configuration, polling/webhook setup, startup, and core shutdown.
Do not create feature-local Bots, Dispatchers, or HTTP sessions.

Startup starts HTTP/database resources, applies pending migrations, ensures the bot's database row, loads modules, and
may synchronize Telegram commands. Polling/webhook startup and shutdown delete the webhook and drop pending updates.
Use controlled configuration and local dependencies for validation instead of starting this runtime as a smoke check.

Shutdown uses `AsyncExitStack` to drain cached work before closing the database, HTTP, bot session, and Redis. Cleanup
failures must not skip other resource closures. Module-owned jobs register router startup/shutdown observers through
manifest hooks; follow the [module lifecycle contract](modules.md).

Give background tasks a strong reference, owner, shutdown path, and error policy. Propagate cancellation and release
resources in context managers or `finally`. Use `TaskGroup` for related fail-fast work; shutdown draining deliberately
uses `gather(return_exceptions=True)`. Shared Last.fm inline loads use shielding so cancellation of one waiter does not
cancel other users of that load. Blocking operations need an async boundary such as `asyncio.to_thread()`.

## HTTP and subprocesses

Reuse the runtime-owned `korone.http.http_client`; inject `HttpClient` into feature clients. Small stateless utilities
may use the shared client directly. Keep parsing network-free and reuse one lookup function across command/callback flows.

Use request-level `RetryPolicy` only when its statuses, attempts, backoff, timeout, redirects, and body-read behavior fit
that operation. Media streaming retry belongs in `MediaDownloader`, with its own limits and truncated-body cleanup.
Do not retry deterministic parsing, authorization, or schema failures.

External commands use `korone.utils.subprocess.run_process` with an explicit timeout. It returns `CompletedProcess` and
terminates/reaps children on timeout or cancellation. Keep format-specific validation and error translation at callers.
FFmpeg's downloader/transform concurrency policies remain in the [media contract](medias.md).

## Cache ownership

| Cache | Owning implementation | Preserve |
| --- | --- | --- |
| JSON results | `korone.utils.cached.Cached` | Shared key construction for reads/reset, serialization, TTL, lock release, tracked background recomputation |
| Media receipts/source IDs | `modules/medias/cache.py` | Versioned keys, ordering, file-ID semantics, corruption-as-miss and Redis failure degradation |
| Last.fm inline contributions | `modules/lastfm/inline.py` | Bounded cache keyed by user and locale, shared in-flight work, expiry and shutdown |

Do not merge caches with different value/invalidation contracts. `Cached` releases lock entries in `finally`; a periodic
lock-cleanup task is unnecessary. Drain background cache work before closing its dependencies.

## Telegram file ownership

Use `modules.utils_.telegram_file.telegram_file` to borrow local Bot API input files read-only or own temporary public
API downloads. Use `download_telegram_file` when a writable destination copy is required. Local files use aiogram's
`wrap_local_file` mapping; unreadable shared storage is a storage error, not a reason to retry HTTP download.

Own upload outputs with `telegram_workspace` until sends/retries finish. Keep `InputFile` objects in domain values;
convert shared `FSInputFile` paths with `telegram_upload` only at Telegram transport boundaries, including albums.
Strings in prepared media represent cached Telegram file IDs, not local paths. Files outside shared storage use multipart.

## Validation

Exercise only affected success, timeout, cancellation, retry, and cleanup paths with controlled dependencies. Check that
files outlive their sends and tasks finish before dependent clients close. Use static checks plus import/load checks
when runtime annotation or lifecycle changes require them; avoid production service writes during reproductions.
