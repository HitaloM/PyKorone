---
name: python-code-standards
description: "Use when generating or reviewing Python code in this project. Follow these standards: comprehensive type hints with modern syntax, snake_case naming, explicit imports, async-first architecture, and strict linting rules enforced by Ruff."
applyTo: "src/korone/**/*.py"
---

# Python Code Standards for PyKorone

This project maintains strict code quality standards using Ruff (line length: 120), Pyright, and comprehensive type hints. These rules apply only to Python application code in `src/korone/`. Match the existing code first, then these conventions.

Module package wiring and loader contract in `.github/instructions/korone-modules-plugin.instructions.md` must be followed for top-level module packages.
Aiogram-specific conventions are documented in `.github/instructions/aiogram-project-patterns.instructions.md`.
Media module conventions are documented in `.github/instructions/medias-module-patterns.instructions.md`.
Development tooling conventions are documented in `.github/instructions/development-tooling.instructions.md`.
Manual locale update and translation review conventions are documented in `.github/instructions/localization-manual-translation.instructions.md`.

## Type Hints & Annotations

### General Rules
- All new and edited function parameters and return types must have type hints
- Use modern Python syntax: `int | None` instead of `Optional[int]`
- Prefer `from __future__ import annotations` in new modules and when editing modules that already use it
- Use `TypeVar` only when a helper genuinely needs a generic type parameter
- Use `TYPE_CHECKING` guards for conditional imports to avoid circular dependencies

### Examples
```python
from __future__ import annotations
from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from some_module import SomeType

T = TypeVar("T")

def process_data(value: int | None, items: list[str]) -> dict[str, Any]:
    """Process data with modern type hints."""
    return {}

async def fetch_async(url: str) -> bytes | None:
    """Async functions must properly annotate return types."""
    pass
```

### ORM Types (SQLAlchemy)
- Use `Mapped[Type]` for ORM annotations
- Declare with proper typing in model classes

```python
from sqlalchemy.orm import Mapped, mapped_column

class Chat(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()
    settings: Mapped[dict[str, Any]] = mapped_column(JSON)
```

## Naming Conventions

### Classes
- **Data Models**: `{Entity}Model` (e.g., `ChatModel`, `UserModel`)
- **Repository Classes**: `{Entity}Repository` (e.g., `ChatRepository`)
- **Handlers**: `{Action}Handler` (e.g., `StartHandler`, `HelpHandler`)
- **Middlewares**: `{Function}Middleware` (e.g., `LocalizationMiddleware`, `SaveChatsMiddleware`)
- **Exceptions**: `{Error}Error` (e.g., `InvalidStateError`)

### Functions & Variables
- Use `snake_case` for all functions and variables
- Private functions: prefix with `_` (e.g., `_internal_process()`)
- Use descriptive names: `get_user_settings()` not `get_us()`

### Constants
```python
from typing import Final

# All caps with underscores, annotated with Final
MAX_MESSAGE_LENGTH: Final[int] = 4096
DEFAULT_LANGUAGE: Final[str] = "en_US"
COMMAND_PREFIX: Final[str] = "/"
```

## Import Organization

### Rules
- **Never** use wildcard imports (`from module import *`)
- Always use explicit imports with clear intent
- Use `__all__` only when a module intentionally defines a public export surface
- Group imports: standard library → third-party → local (3 groups, blank lines between)
- For database/ORM imports, use `TYPE_CHECKING` when appropriate to avoid runtime overhead

### Example
```python
from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram import Router
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from korone.db.models.chat import ChatModel
from korone.logger import get_logger

if TYPE_CHECKING:
    from aiogram.types import Message

logger = get_logger(__name__)
router = Router(name="example")
```

### Repository Pattern
All database access must go through repositories. Use static methods:
```python
class UserRepository:
    @staticmethod
    async def get_by_id(session: Session, user_id: int) -> User | None:
        result = await session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create(session: Session, **kwargs: Any) -> User:
        user = User(**kwargs)
        session.add(user)
        await session.flush()
        return user
```

### Handlers
Extend project handler bases from `korone.utils.handlers` and follow naming patterns:
```python
from korone.utils.handlers import KoroneMessageHandler


class StartHandler(KoroneMessageHandler):
    """Handle /start command."""

    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return CommandStart(), PrivateChatFilter()

    async def handle(self) -> None:
        """Process start command."""
        await self.answer("Welcome!")
```

## Async-First Architecture

- Prefer async code for database and network I/O (`async def`, `await`)
- Keep pure computations synchronous
- Use `asyncio` for concurrency when it improves the implementation
- aiogram routers are the entry point for handlers

## Documentation & Comments

### Docstrings
- Keep docstrings minimal; rely on type hints for clarity
- Use one-line docstrings for simple functions
- Use multi-line for complex logic, but prefer self-documenting code

```python
def calculate_stats(data: dict[str, int]) -> int:
    """Return total of all values."""
    return sum(data.values())

async def complex_operation(session: Session, filters: dict[str, Any]) -> list[Result]:
    """Fetch and process results with applied filters.

    Args:
        session: Database session
        filters: Query filters to apply

    Returns:
        List of processed results
    """
    # Implementation
    pass
```

### Structured Logging
Use the project logger helpers and structured keyword arguments for all logging:
```python
from korone.logger import get_logger

logger = get_logger(__name__)

async def on_user_created(user_id: int, username: str) -> None:
    await logger.ainfo("user_created", user_id=user_id, username=username)


def on_startup() -> None:
    logger.info("startup", service="korone")
```

## Code Patterns

### Dataclasses with Slots
Use `slots=True` for memory efficiency:
```python
from dataclasses import dataclass

@dataclass(slots=True)
class Config:
    token: str
    debug: bool = False
```

### Caching
Use the `@Cached` decorator for expensive operations:
```python
from korone.utils.cached import Cached

class SettingsRepository:
    @Cached()
    @staticmethod
    async def get_settings(user_id: int) -> dict[str, Any]:
        # Expensive database query
        pass
```

### Validators
Use Pydantic `@field_validator` for validation:
```python
from pydantic import BaseModel, field_validator

class ChatConfig(BaseModel):
    language: str
    timezone: str

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        if v not in SUPPORTED_LANGUAGES:
            msg = f"Unsupported language: {v}"
            raise ValueError(msg)
        return v
```

## Code Quality Standards

### Linting Rules (Ruff)
This project uses Ruff with strict rules:
- **Line length**: 120 characters (enforced)
- **Docstring code formatting**: Enabled
- **Typing rules (ANN)**: All new and edited functions must have type hints
- **Import sorting (I)**: Enforced by Ruff
- **Performance (PERF)**: Pythonic code patterns
- **Simplification (SIM)**: Prefer simple over complex
- **Slots (SLOT)**: Dataclasses should use slots

### Pre-commit Hooks
Before committing, the following checks run:
1. Ruff check with `--fix`, `--preview`, and `--unsafe-fixes`
2. Ruff formatting
3. Use Pyright locally when a change affects typing or public APIs

### Test Coverage
While not enforced here, maintain clear, testable code by:
- Separating concerns (handlers, repositories, services)
- Using dependency injection where appropriate
- Avoiding side effects in pure functions

## Common Pitfalls to Avoid

❌ **Don't**:
```python
# Wildcard imports
from utils import *

# Missing type hints
def process(data):
    return data

# Ignoring linting warnings
result = x=5  # Should be x = 5

# Hardcoded values without constants
if user_role == "admin":  # Should use constant

# Not awaiting async functions
result = some_async_function()
```

✅ **Do**:
```python
# Explicit imports
from korone.utils import process

# Complete type hints
def process(data: dict[str, Any]) -> dict[str, Any]:
    return data

# Follow formatting
result = x = 5

# Use constants
if user_role == ADMIN_ROLE:
    pass

# Properly await
result = await some_async_function()
```

### Configuration Files

These standards are enforced by:
- **Ruff**: `ruff.toml` (line length 120, rules in `[lint]`)
- **Pre-commit**: `.pre-commit-config.yaml` runs Ruff check and Ruff format
- **Pyright**: use it locally when a change affects typing or public APIs

---

**Questions?** Refer to the codebase examples in `src/korone/` for patterns in action.
