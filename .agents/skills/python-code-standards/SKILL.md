---
name: python-code-standards
description: Use when generating, editing, or reviewing Python code in this project, especially under src/korone. Follow comprehensive type hints with modern syntax, snake_case naming, explicit imports, async-first architecture, repository-based database access, project handler bases, structured logging, and strict Ruff/Pyright expectations.
---

# Python Code Standards for PyKorone

This project maintains strict code quality standards using Ruff, Pyright, and comprehensive type hints. Match the existing code first, then these conventions.

For top-level module package wiring, also use `.agents/skills/korone-modules-plugin-contract/SKILL.md`. For aiogram-specific code, also use `.agents/skills/aiogram-project-patterns/SKILL.md`. For handlers, also use `.agents/skills/bot-handler-development/SKILL.md`. For media module code, also use `.agents/skills/medias-module-patterns/SKILL.md`.

## Type Hints and Annotations

- All new and edited function parameters and return types must have type hints.
- Use modern Python syntax: `int | None` instead of `Optional[int]`.
- Prefer Python 3.14 type parameter syntax such as `def first[T](...)` and `class Cache[T]` for new generics.
- Keep `TypeVar`, `ParamSpec`, or compatibility forms only when framework interoperability or nearby code requires them.
- Use `TYPE_CHECKING` guards for conditional imports to avoid circular dependencies.

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from some_module import SomeType


def first[T](items: list[T]) -> T | None:
    return items[0] if items else None


def describe(item: SomeType) -> str:
    return str(item)
```

## ORM Types

- Use `Mapped[Type]` for SQLAlchemy ORM annotations.
- Declare columns with proper typing in model classes.

```python
from sqlalchemy import BigInteger
from sqlalchemy.orm import Mapped, mapped_column


class ChatModel(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, unique=True)
```

## Naming Conventions

- Data models: `{Entity}Model`.
- Repository classes: `{Entity}Repository`.
- Handlers: `{Action}Handler`.
- Middlewares: `{Function}Middleware`.
- Exceptions: `{Error}Error`.
- Functions and variables: `snake_case`.
- Private helpers: prefix with `_`.
- Constants: uppercase with underscores and `Final` when appropriate.

```python
from typing import Final

MAX_MESSAGE_LENGTH: Final[int] = 4096
DEFAULT_LANGUAGE: Final[str] = "en_US"
```

## Import Organization

- Never use wildcard imports.
- Always use explicit imports with clear intent.
- Use `__all__` only when a module intentionally defines a public export surface.
- Group imports as standard library, third-party, then local, with blank lines between groups.
- For database/ORM imports, use `TYPE_CHECKING` when appropriate to avoid runtime overhead.

```python
from typing import TYPE_CHECKING

from korone.logger import get_logger

if TYPE_CHECKING:
    from aiogram.types import Message

logger = get_logger(__name__)


async def log_message(message: Message) -> None:
    await logger.adebug("message_received", message_id=message.message_id)
```

## Repository Pattern

All database access must go through repositories. Existing repositories usually expose static methods and own their transaction with `session_scope()`. When adding repository helpers, follow the nearby repository style before introducing explicit session parameters.

```python
from sqlalchemy import func, select

from korone.db.base import get_one
from korone.db.models.chat import ChatModel
from korone.db.session import session_scope


class ChatRepository:
    @staticmethod
    async def get_by_chat_id(chat_id: int) -> ChatModel | None:
        async with session_scope() as session:
            return await get_one(session, ChatModel, ChatModel.chat_id == chat_id)

    @staticmethod
    async def total_count() -> int:
        async with session_scope() as session:
            result = await session.execute(select(func.count()).select_from(ChatModel))
            return result.scalar_one() or 0
```

## Handlers

- Follow `.agents/skills/bot-handler-development/SKILL.md` instead of duplicating handler architecture here.
- Extend the project bases from `korone.utils.handlers`; do not assume helpers exist across all three bases.
- Use `self.event.reply(...)` for `KoroneMessageHandler`, callback helpers for `KoroneCallbackQueryHandler`, and `self.answer(...)` only for `KoroneMessageCallbackQueryHandler`.

## Async-First Architecture

- Prefer async code for database and network I/O.
- Keep pure computations synchronous.
- Use `asyncio` for concurrency when it improves the implementation.
- aiogram routers are the entry point for handlers.

## Documentation and Comments

- Keep docstrings minimal; rely on type hints for clarity.
- Use one-line docstrings for simple functions.
- Use multi-line docstrings only for complex logic.
- Add code comments sparingly where they clarify non-obvious behavior.

## Structured Logging

Use project logger helpers and structured keyword arguments for logging.

```python
from korone.logger import get_logger

logger = get_logger(__name__)


async def on_user_created(user_id: int, username: str) -> None:
    await logger.ainfo("user_created", user_id=user_id, username=username)
```

## Code Patterns

- Use `@dataclass(slots=True)` for dataclasses.
- Use the `@Cached` decorator for expensive operations when it matches existing cache patterns.
- Use Pydantic `@field_validator` for Pydantic model validation.

```python
from dataclasses import dataclass


@dataclass(slots=True)
class Config:
    token: str
    debug: bool = False
```

```python
from pydantic import BaseModel, field_validator


class ChatConfig(BaseModel):
    language: str

    @field_validator("language")
    @classmethod
    def validate_language(cls, value: str) -> str:
        if value not in SUPPORTED_LANGUAGES:
            msg = f"Unsupported language: {value}"
            raise ValueError(msg)
        return value
```

## Quality Standards

- Ruff line length is 120 characters.
- Ruff enforces type annotations, import sorting, performance, simplification, dataclass slots, and other strict lint rules.
- Before committing, pre-commit runs Ruff check with fix, preview, and unsafe fixes, then Ruff format.
- Use Pyright locally when a change affects typing or public APIs.

## Pitfalls to Avoid

- Wildcard imports.
- Missing type hints on new or edited functions.
- Ignoring lint warnings.
- Hardcoded repeated values that should be named constants.
- Forgetting `await` on async calls.
- Bypassing repository classes for database access.
