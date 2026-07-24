# Python Standards

Apply these rules to new and edited Python. Match nearby code before introducing a new abstraction.

## Version and Syntax

- Treat the minimum Python version configured in `pyproject.toml` and `.python-version` as authoritative.
- Use syntax supported by that minimum version; do not introduce features from a newer development release.
- Prefer built-in generics and unions, such as `list[str]`, `dict[str, int]`, and `str | None`.
- Use PEP 695 syntax for new generics and aliases: `class Cache[T]`, `def first[T](...)`, and `type CacheKey = str`.
- Keep `TypeVar`, `ParamSpec`, and compatibility aliases only when required by a framework, public API, or nearby code.
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

- Use dataclasses for internal value objects. Add `slots=True`, `frozen=True`, or `kw_only=True` when each option matches the object's contract.
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

- Prefer async code for database and network I/O; keep pure computation synchronous.
- Keep SQLAlchemy access and transaction ownership in repository classes.
- Follow the nearest repository's session pattern before adding explicit session parameters.
- Keep handlers focused on Telegram orchestration and move reusable business logic, transport, parsing, and persistence to focused layers.
- Use shared project abstractions before creating parallel ones.

## Async and Resource Safety

- Prefer `asyncio.TaskGroup` for related concurrent work and `asyncio.timeout()` for bounded operations.
- Propagate `asyncio.CancelledError`; use `try`/`finally` when cancellation must release resources.
- Use `asyncio.to_thread()` for blocking I/O that cannot be made asynchronous. Measure before offloading CPU work.
- Do not create orphan background tasks. Keep a strong reference and give each task an explicit owner, shutdown path, and error policy.
- Use synchronous or asynchronous context managers for files, locks, sessions, responses, and other resources.
- Do not rely on the GIL to protect shared mutable state. Use explicit synchronization when code may run across threads.

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
