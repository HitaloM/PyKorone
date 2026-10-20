# Python boundaries

Use this reference for typing, runtime annotations, and abstraction choices. Read supported/local Python versions from
`pyproject.toml` and `.python-version`; the latter selects the development interpreter, not the supported minimum.

## Typing and runtime inspection

- Fully annotate new and edited functions with modern unions, built-in generics, and PEP 695 aliases/generics.
  `KoroneBaseHandler` deliberately retains `TypeVar`: aiogram's `Generic`/`ABC` hierarchy requires it at runtime.
- Python 3.14 defers annotations. Do not add `from __future__ import annotations`; use `annotationlib.get_annotations()`
  when inspecting them. Keep imports available at runtime when frameworks, Pydantic, or SQLAlchemy resolve those types.
- Narrow untrusted `object` values. Keep `Any`, casts, and suppressions at demonstrated dynamic framework boundaries;
  do not use them to hide data-flow defects. The manifest's `ModuleHandler` is one such aiogram decorator boundary.
- Use standard-library dataclasses for internal values and Pydantic for external validation/settings. Apply frozen,
  slotted, or keyword-only options according to the object's contract; framework/ORM objects have different needs.
- Import abstract collection types from `collections.abc`. Use explicit exports only for an intentional public surface.
  Let `ruff.toml` enforce mechanical naming, import, formatting, and modernization rules.

## Ownership and abstraction

The normal flow is middleware context → filters/typed arguments → project handler → feature logic → repository or
transport. Compose UI independently and render it at the Telegram payload boundary.

Keep shared Telegram integration in `modules/utils_`, runtime infrastructure in `korone.utils`, and domain behavior in
its owning module. Use functions for stateless operations and classes for resources or domain/framework interfaces.
Similar constructors or loops do not justify a generic service/base class; require a concrete shared policy.
Do not move packages solely to standardize names or add forwarding APIs to unrelated repositories.

Use structured logging through `korone.logger.get_logger`. Catch errors where recovery or translation is owned, preserve
exception chaining, and let unexpected defects reach centralized handling. Avoid repeated exception logging and secrets
or sensitive payloads in log fields.

Read [persistence.md](persistence.md) for transactions/ID namespaces and [runtime.md](runtime.md) for async resources,
HTTP, subprocesses, caches, and files. These contracts do not need to be loaded for a pure Python typing edit.
