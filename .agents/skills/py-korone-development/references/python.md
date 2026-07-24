# Python Standards

Apply these rules to new and edited Python. Match nearby code before introducing a new abstraction.

## Types and Names

- Add complete parameter and return annotations to every new or edited function.
- Use modern syntax such as `int | None` and Python 3.14 type parameters for new generics.
- Keep compatibility forms such as `TypeVar` only when framework interoperability or nearby code requires them.
- Use `Mapped[T]` and `mapped_column(...)` for SQLAlchemy ORM fields.
- Use `{Entity}Model`, `{Entity}Repository`, `{Action}Handler`, `{Function}Middleware`, and `{Error}Error`.
- Use `snake_case` for functions and variables, a leading underscore for private helpers, and uppercase `Final` constants.

## Imports and Exports

- Use explicit imports; never use wildcard imports.
- Group standard-library, third-party, and local imports.
- Use `TYPE_CHECKING` to avoid runtime-only typing imports and circular dependencies.
- Define `__all__` only for an intentional public export surface.

## Architecture

- Prefer async code for database and network I/O; keep pure computation synchronous.
- Keep SQLAlchemy access and transaction ownership in repository classes.
- Follow the nearest repository's session pattern before adding explicit session parameters.
- Keep handlers focused on Telegram orchestration and move reusable business logic, transport, parsing, and persistence to focused layers.
- Use shared project abstractions before creating parallel ones.

## Logging and Errors

- Create loggers with `korone.logger.get_logger`.
- Use structured keyword fields and the async logger methods where appropriate.
- Catch only errors the current layer can recover from or translate.
- Preserve cancellation and let unexpected defects reach centralized error handling.
- Never log secrets or full sensitive payloads.

## Code Style

- Prefer `@dataclass(slots=True)` for dataclasses.
- Use Pydantic validators supported by the active dependency range.
- Keep docstrings and comments concise; explain only non-obvious contracts or decisions.
- Read active Python and dependency versions from `.python-version` and `pyproject.toml`; do not rely on versions copied into documentation.
- Treat Ruff and Pyright diagnostics as defects to resolve, not warnings to bypass with broad ignores or casts.

## Avoid

- Missing annotations, wildcard imports, forgotten `await`, or blocking I/O in async paths.
- Direct database access outside repositories.
- New compatibility shims without an active compatibility requirement.
- Hardcoded repeated values that should be named constants.
- Unrelated refactors or formatting churn.
