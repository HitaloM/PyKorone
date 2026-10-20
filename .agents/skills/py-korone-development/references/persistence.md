# Persistence and migrations

Read `src/korone/db/session.py`, the owning repository/model, and its consumers before changing a persistence contract.

## Repository ownership

- Keep feature SQL behind repositories in `src/korone/db/repositories/`. Operational SQL for bootstrap, migrations, and
  PostgreSQL statistics belongs in database infrastructure.
- A repository method owns `session_scope()`: success commits, failure rolls back, and returned values must be usable
  after the session closes. Do not return live query results or require handlers to own transactions.
- Keep related statements atomic. For example, replacing admins and switching a default sticker pack require one
  transaction. Preserve query ordering, uniqueness/upsert behavior, and relevant constraints.
- Use `get_one` from `korone.db.base` for optional predicate lookups; use `session.scalar(statement.limit(1))` for an
  ordered first row. ORM fields use `Mapped[T]` / `mapped_column(...)`.
- Use the entity's owning repository. `ChatTopicRepository` and `UserInGroupRepository` own their rows even though they
  share `chat.py` with `ChatRepository`. Resolve a sticker pack in the feature flow and write through its selected pack ID.

## ID namespaces

`ChatModel.chat_id` is a Telegram ID; `ChatModel.id` is a database primary key. Column names alone are insufficient:
admin/membership `chat_id`, `user_id`, and `group_id` foreign keys can reference `chats.id`. Inspect the model and caller.

Use `ChatRepository.get_by_chat_id(...)` for Telegram identity and `get_by_id(...)` for known database foreign keys.
Never try one and fall back to the other with the same integer. Public admin helpers take Telegram IDs; resolve model
relationships explicitly before calling Telegram or writing foreign keys.

## Schema changes

Review `alembic/env.py`, existing revisions, `src/korone/db/utils.py`, and the relevant Makefile targets.
Generate with `make db_revision m="message"` against the intended development database and manually inspect the result.
Check constraints, defaults, data backfills, nullability, and downgrade behavior where applicable.

Preserve URL resolution for Alembic and runtime. Alembic intentionally bootstraps an isolated `korone` namespace so schema
tooling can load models without constructing the Telegram bot. Normal startup may apply pending migrations; do not use
bot startup merely to validate a revision.

## Validation

Use a deterministic local reproduction for changed lookups, ordering, ID resolution, and transaction behavior. Validate
migration metadata and affected upgrade/downgrade paths against a disposable database when available; report if actual
migration execution was unavailable. Run relevant Ruff and Pyright checks. Do not mutate a deployment database as an
incidental documentation or static-check step.
