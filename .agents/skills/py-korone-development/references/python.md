# Python Standards

Apply these rules to new and edited Python. Read nearby implementations for domain details and use the boundaries
below when choosing an abstraction.

## Version and Syntax

- Treat the minimum Python version configured in `pyproject.toml` and `.python-version` as authoritative.
- Use syntax supported by that minimum version; do not introduce features from a newer development release.
- Prefer built-in generics and unions, such as `list[str]`, `dict[str, int]`, and `str | None`.
- Use PEP 695 syntax for new generics and aliases: `class Cache[T]`, `def first[T](...)`, and `type CacheKey = str`.
- Keep legacy generics only for a demonstrated framework requirement. `KoroneBaseHandler` needs `TypeVar` because
  modern generic syntax conflicts with aiogram's `Generic`/`ABC` inheritance at runtime.
- Use structural pattern matching for genuinely structural or discriminated data, not as a replacement for a simple conditional.
- Use template strings only with an explicit renderer that safely processes them; use f-strings for ordinary interpolation.

## Annotations and Typing

- Add complete parameter and return annotations to every new or edited function.
- Do not add `from __future__ import annotations`; Python 3.14 defers annotation evaluation by default.
- Avoid quoted forward references unless an API explicitly requires a string.
- Use `annotationlib.get_annotations()` when runtime code must inspect annotations; do not depend on annotation internals.
- Put imports behind `TYPE_CHECKING` only when the imported symbol is never needed by runtime introspection, Pydantic, SQLAlchemy, or a framework.
- Import runtime protocols and abstract collection types from `collections.abc`.
- Use `Self` for fluent or alternative constructors, `@override` for intentional overrides, and `ClassVar` for class-level state.
- Use `TypeIs` for type-narrowing predicates when both branches can be narrowed; reserve `TypeGuard` for its distinct compatibility semantics.
- Use `Never` and `assert_never()` to make closed branches exhaustive.
- Use `Protocol` for structural interfaces and `TypedDict` for statically shaped mappings; use `Required`, `NotRequired`, and `ReadOnly` when their contracts matter.
- Prefer `Literal` or `StrEnum` to free-form strings for small closed domains.
- Accept `object` and narrow it at untrusted boundaries. Use `Any` only for genuinely dynamic APIs.
- Use `cast()` only after validation or for a documented invariant the type checker cannot infer.

## Data Modeling and Names

- Use standard-library dataclasses for internal value objects; do not import a transitive `attrs` dependency. Add `slots=True`, `frozen=True`, or `kw_only=True` when each option matches the object's contract.
- Do not force slotted or frozen dataclasses onto ORM, Pydantic, framework-managed, or dynamically attributed objects.
- Use `Mapped[T]` and `mapped_column(...)` for SQLAlchemy ORM fields.
- Use Pydantic models at validation, serialization, settings, and external-data boundaries; use APIs supported by the active dependency range.
- Use `{Entity}Model`, `{Entity}Repository`, `{Action}Handler`, `{Function}Middleware`, and `{Error}Error`.
- Use `snake_case` for functions and variables and a leading underscore for private helpers.
- Use uppercase names for module constants. Add `Final` when preventing reassignment communicates a useful invariant.

## Imports and Exports

- Use explicit imports; never use wildcard imports.
- Group standard-library, third-party, and local imports.
- Define `__all__` only for an intentional public export surface.

## Architecture

- The normal update path is middleware context → filters/arguments → project handler → feature logic → repository
  or transport. Compose UI separately and render it at the Telegram payload boundary.
- Keep shared Telegram integration in `modules/utils_`, runtime infrastructure in `korone.utils`, and domain logic
  inside its owning module. Do not move directories solely to standardize their names.
- Use functions for stateless operations and classes for resources, framework entry points, or domain interfaces.
  Similar constructors or small loops alone do not justify a generic base class or a universal service layer.
- Prefer async code for database and network I/O; keep pure computation synchronous.
- Feature SQL and transaction ownership belong in repositories. Operational SQL for bootstrap, migration, and
  PostgreSQL statistics belongs in database infrastructure.
- Repository methods own `session_scope()` transactions: success commits and failure rolls back. Do not return live
  query results or require feature callers to open sessions.
- Use the entity's repository directly; do not add forwarding methods to `ChatRepository` for topics or memberships.
  Use `get_one` for optional predicate-based row lookup and `session.scalar(statement.limit(1))` for ordered queries.
  Preserve ordering and multi-statement transaction boundaries. Resolve sticker-pack titles in the feature flow and
  use the selected pack ID for writes rather than maintaining parallel repository APIs.
- Public admin helpers accept Telegram IDs. Resolve database foreign keys explicitly with `get_by_id`; never guess
  whether an incoming number is a Telegram ID or a database key.
- Keep handlers focused on Telegram orchestration and move reusable business logic, transport, parsing, and persistence to focused layers.
- Use shared project abstractions before creating parallel ones.

## Async and Resource Safety

- Prefer `asyncio.TaskGroup` for related concurrent work and `asyncio.timeout()` for bounded operations.
  Shared inline loads use shielding so one waiter cannot cancel work needed by others; shutdown draining uses
  `gather(return_exceptions=True)` deliberately rather than fail-fast grouping.
- Propagate `asyncio.CancelledError`; use `try`/`finally` when cancellation must release resources.
- Use `asyncio.to_thread()` for blocking I/O that cannot be made asynchronous. Measure before offloading CPU work.
- Do not create orphan background tasks. Keep a strong reference and give each task an explicit owner, shutdown path, and error policy.
- Use synchronous or asynchronous context managers for files, locks, sessions, responses, and other resources.
- External commands use `korone.utils.subprocess.run_process` with an explicit timeout. It captures output, returns
  `CompletedProcess`, and terminates/reaps children on timeout or cancellation. Keep format conversion and
  feature-specific error translation at the caller; do not duplicate child-process termination logic.
- Preserve distinct cache contracts: JSON results (`Cached`), versioned media receipts/source IDs (`MediaCache`),
  and bounded user/locale-specific inline contributions. Their serialization and invalidation policies differ.
  Keep keys and TTL semantics stable and share key construction with invalidation. `Cached` releases lock entries
  in `finally`, so no periodic cleanup task is needed; drain its background tasks before closing dependent clients.
- Do not rely on the GIL to protect shared mutable state. Use explicit synchronization when code may run across threads.

## HTTP and Files

- Reuse the runtime-owned `http_client`; inject `HttpClient` into feature clients. Small stateless utilities may
  use the shared client directly. Do not create a session per request or handler.
- Keep requests in feature clients/utilities and parsing deterministic. Commands and callbacks for the same lookup
  use one function, as with `web.utils.ip.fetch_ip_info`.
- Use request-level `RetryPolicy` for metadata when appropriate; media streaming retry remains in `MediaDownloader`.
  Their body-reading, size-limit, and recovery requirements differ.
- Use `modules.utils_.telegram_file.download_telegram_file` to preserve local Bot API storage and network fallback.
  Do not add feature-local aliases without additional policy.
- Use `Path` methods directly and pass serialized bytes to `BufferedInputFile`; avoid forwarding wrappers or
  decode/encode round trips that add no behavior.

## Logging and Errors

- Create loggers with `korone.logger.get_logger`.
- Use structured keyword fields and the async logger methods where appropriate.
- Catch only errors the current layer can recover from or translate.
- Chain translated exceptions with `raise ... from exc`.
- Use `ExceptionGroup` and `except*` only when concurrent operations can produce multiple independent failures.
- Log failures at the layer that owns the recovery policy; avoid logging the same exception repeatedly.
- Let unexpected defects reach centralized error handling.
- Never log secrets or full sensitive payloads.

## Idioms and Validation

- Prefer `pathlib.Path` for filesystem paths and timezone-aware `datetime` values for persisted or exchanged timestamps.
- Prefer direct iteration, comprehensions, generator expressions, unpacking, and assignment expressions when they make intent clearer.
- Keep side effects out of comprehensions and avoid dense expressions that obscure control flow.
- Keep docstrings and comments concise; explain only non-obvious contracts or decisions.
- Treat Ruff and Pyright diagnostics as defects to resolve, not warnings to bypass with broad ignores or casts.
- Measure performance before adding caching, low-level optimization, threads, processes, subinterpreters, or free-threaded-specific code.

## Avoid

- Missing annotations, wildcard imports, forgotten `await`, or blocking I/O in async paths.
- Direct database access outside repositories.
- New compatibility shims without an active compatibility requirement.
- Hardcoded repeated values that should be named constants.
- Mutable default arguments, broad exception catches, silent error suppression, and implicit resource cleanup.
- Unrelated refactors or formatting churn.
