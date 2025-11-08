# AI Development Guidelines for Sophie Bot

This document serves as a comprehensive guide for AI-assisted development on the Sophie Bot project. Read this document
carefully before starting work on any new features or modifications.

## Code Style and Paradigms

### PEP8 Compliance

- Follow PEP8 standards strictly
- Use 120 character line length (configured in pyproject.toml)
- Use Black formatter with `--preview` flag for consistent code formatting
- Use isort with Black profile for import sorting
- Use pycln for removing unused imports
- Place all imports at the top of the module; do not import inside functions or conditional blocks

### Type Safety

- **ALWAYS** use type annotations for all function parameters and return values
- The project is tested against mypy - all code must pass mypy type checking
- Use `from __future__ import annotations` for forward references when needed
- Prefer strict typing with `Union` types over `Any`
- Example:

```python
from typing import Optional
from aiogram.types import Message


async def handle_message(message: Message, user_id: int) -> Optional[str]:
    return message.text
```

### Functional Programming Style

- **Default paradigm for this project is functional programming**
- Prefer pure functions without side effects when possible
- Use async/await patterns extensively
- Avoid global state modifications
- Use immutable data structures when applicable
- Leverage higher-order functions and function composition
- Example functional approach:

```python
async def process_message(message: Message) -> dict[str, str]:
    return {
        "text": message.text or "",
        "user": message.from_user.full_name if message.from_user else "Unknown"
    }
```

## Translation System

The project uses a dual translation system:

### Crowdin Integration

- Main translation management through Crowdin platform
- Configuration in `crowdin.yml`
- Two translation formats supported:
    1. **YAML files**: `sophie_bot/localization/en.yaml` → `sophie_bot/localization/{locale}.yaml`
    2. **Gettext POT/PO**: `locales/sophie.pot` → `locales/{locale}/LC_MESSAGES/sophie.po`

### Making Text Translatable

- **ALWAYS** use the i18n system for user-facing text
- Import translation functions:

```python
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_
```

- Use `_()` for runtime translation and `l_()` for lazy translation (e.g., in decorators)
- Example:

```python
@flags.help(description=l_("Translates text to the chat's selected language"))
async def translate_command():
    await message.reply(_("Translation completed"))
```

### Translation Workflow

- Extract strings: `make extract_lang`
- Update translations: `make update_lang`
- Compile translations: `make compile_lang`
- Full locale workflow: `make locale`

## Make Tools

### Essential Commands

- **`make commit`**: **ALWAYS run this after every task** - runs all required checks:
    - `fix_code_style`: Auto-fixes code formatting
    - `extract_lang`: Extracts translatable strings
    - `test_code_style`: Checks code style compliance
    - `test_codeanalysis`: Runs mypy type checking
    - `run_tests`: Executes pytest test suite
    - `gen_wiki`: Generates project wiki

### Individual Tools

- `make fix_code_style`: Auto-format code (pycln + isort + black)
- `make test_code_style`: Check code style without fixing
- `make test_codeanalysis`: Run mypy type checker
- `make run_tests`: Run pytest with Allure reporting
- `make locale`: Full translation workflow
- `make new_lang LANG=xx_XX`: Create new language support
- `make gen_wiki`: Generate project documentation

## Project Structure

### Directory Organization

```
sophie_bot/
├── args/              # Argument parsing utilities
├── db/
│   ├── cache/         # Caching mechanisms
│   └── models/        # Database models (Beanie ORM)
├── filters/           # Custom aiogram filters
├── localization/      # Translation YAML files
├── middlewares/       # Aiogram middlewares
├── modules/           # Feature modules
│   └── {module_name}/
│       ├── handlers/      # Command handlers
│       ├── utils/         # Utility functions
│       ├── filters/       # Module-specific filters
│       ├── middlewares/   # Module-specific middlewares
│       ├── magic_handlers/# Special handlers
│       └── fsm/          # Finite State Machine states
├── services/          # External service integrations
└── utils/             # Global utilities
```

### Creating New Modules

1. Create directory: `sophie_bot/modules/{module_name}/`
2. Add required subdirectories: `handlers/`, `utils/`
3. Create `handlers/__init__.py` with handler classes
4. Follow existing patterns from other modules
5. Register handlers in the main bot initialization

### Handler Structure

All handlers should inherit from aiogram's base handlers and use the established patterns:

```python
from aiogram import flags
from aiogram.handlers import MessageHandler
from aiogram.types import Message
from ass_tg.types import TextArg
from stfu_tg import Doc, Title

from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.utils.i18n import gettext as _


@flags.help(description=l_("Command description"))
@flags.disableable(name="command_name")
class MyHandler(MessageHandler):
    @staticmethod
    def filters():
        return (CMDFilter(("command", "alias")),)

    async def handle(self):
        # Handler logic here
        pass
```

## Required Libraries Usage

### ASS (Argument Searcher of Sophie)

- **ALWAYS use ASS for parsing user arguments**
- Import: `from ass_tg.types import TextArg, IntArg, UserArg, etc.`
- Define argument parsing in handler methods
- Example:

```python
from ass_tg.types import TextArg, IntArg


async def get_args(message: Message, _data: dict):
    return {
        "text": TextArg(l_("Text to process")),
        "count": IntArg(l_("Number of items"), default=1)
    }
```

### STFU (Sophie Text Formatting Utility)

- **ALWAYS use STFU for text formatting**
- Import: `from stfu_tg import Doc, Title, Bold, Section, PreformattedHTML, etc.`
- Build structured documents instead of manual string formatting
- Example:

```python
from stfu_tg import Doc, Title, Bold, Section

doc = Doc(
    Title(_("Command Result")),
    KeyValue(_("Status"), _("Success")),
    Section(_("Operation completed"), title=_("Details"))
)
await message.reply(str(doc))
```

## Core Libraries

### Primary Dependencies

- **aiogram 3.21+**: Telegram Bot API framework
- **stfu-tg 3.4+**: Text formatting utility (in-house)
- **ass-tg 2.4.3**: Argument parsing system (in-house)
- **beanie 2+**: MongoDB ODM built on Pydantic
- **pydantic 2+**: Data validation and settings management
- **pydantic-ai-slim**: AI integration framework
- **motor 3.6+**: Async MongoDB driver
- **redis 6+**: Redis client for caching

### Development Dependencies

- **mypy 1.11+**: Static type checker
- **black 24+**: Code formatter
- **isort**: Import sorter
- **flake8 7+**: Linting
- **pytest 8.3+**: Testing framework
- **pycln 2.1+**: Unused import remover

### AI and ML Libraries

- **openai 1+**: OpenAI API client
- **pydantic-ai-slim**: AI agent framework
- **lingua-language-detector 2+**: Language detection
- **numpy 2+**: Numerical computations

### Utility Libraries

- **structlog 25+**: Structured logging
- **babel 2.16+**: Internationalization
- **ujson 5.1+**: Fast JSON parsing
- **redis**: Caching and session storage
- **apscheduler 3.11+**: Task scheduling

## Development Workflow

1. **Setup**: Ensure Python 3.12+, Poetry, MongoDB, and Redis are installed
2. **Dependencies**: `poetry install`
3. **Configuration**: Copy and edit `data/config.example.env` to `data/config.env`
4. **Development**: Write code following these guidelines
5. **Testing**: Run `make commit` to validate all changes
6. **Submission**: Ensure all tests pass before committing

## Database and Chat ID Conventions

### Chat ID Naming Convention

The Sophie Bot project uses two distinct types of chat identifiers that **must not be confused**:

#### chat_tid (Telegram Chat ID)
- **Type**: `int`  
- **Source**: Telegram's API (`message.chat.id`, `chat.id`)
- **Usage**: External API calls, user-facing operations, handler parameters
- **Example**: `-1001234567890` (supergroup), `123456789` (private chat)

#### chat_iid (Internal Database ID)
- **Type**: `PydanticObjectId` (Beanie/MongoDB ObjectId)
- **Source**: Database document primary key (`chat_model.id`)  
- **Usage**: Internal database relationships, Link<ChatModel> queries
- **Example**: `ObjectId('507f1f77bcf86cd799439011')`

### Database Model Patterns

#### ChatModel Structure
```python
class ChatModel(Document):
    chat_id: Annotated[int, Indexed(unique=True)]  # Telegram chat ID (chat_tid)
    # ... other fields
    # self.id is the PydanticObjectId (chat_iid)
```

#### Link Relationships (CRITICAL)
When using `Link[ChatModel]` relationships, **always** use the database object ID (`chat_iid`):

```python
# ✅ CORRECT - Link relationship with database object ID
class SomeModel(Document):
    chat: Link[ChatModel]

# Find by Link relationship
model = await SomeModel.find_one(SomeModel.chat.id == chat_model.id)  # chat_iid
```

#### Method Parameter Naming
```python
# ✅ CORRECT - Clear parameter naming
async def get_settings(chat_tid: int) -> SomeModel:
    """Get settings using Telegram chat ID."""
    chat = await ChatModel.get_by_chat_id(chat_tid)  # Convert to ChatModel
    if not chat:
        raise ValueError(f"Chat with ID {chat_tid} not found")
    
    return await SomeModel.find_one(SomeModel.chat.id == chat.id)  # Use chat_iid

async def get_by_internal_id(chat_iid: PydanticObjectId) -> SomeModel:
    """Get settings using database internal ID."""
    return await SomeModel.find_one(SomeModel.chat.id == chat_iid)
```

### Common Mistakes to Avoid

#### ❌ WRONG - Mixing ID types in Link queries
```python
# This will FAIL - using Telegram ID in Link query
chat_tid = message.chat.id  # Telegram ID (int)
model = await SomeModel.find_one(SomeModel.chat.id == chat_tid)  # WRONG!
```

#### ✅ CORRECT - Proper ID conversion
```python
# Convert Telegram ID to database model first
chat_tid = message.chat.id  # Telegram ID (int)
chat = await ChatModel.get_by_chat_id(chat_tid)  # Get ChatModel
model = await SomeModel.find_one(SomeModel.chat.id == chat.id)  # Use chat_iid
```

### Handler Best Practices

```python
@flags.help(description=l_("Example handler"))
class ExampleHandler(SophieMessageHandler):
    async def handle(self) -> Any:
        # Get Telegram chat ID from connection
        chat_tid = self.connection.id  # This is Telegram's chat ID
        
        # For Link queries, get the ChatModel first
        chat = await ChatModel.get_by_chat_id(chat_tid)
        if not chat:
            return await self.event.reply(_("Chat not found"))
        
        # Use chat.id (database object ID) for Link queries
        model = await SomeModel.find_one(SomeModel.chat.id == chat.id)
```

### Variable Naming in Code

- Use `chat_tid` for Telegram chat ID variables
- Use `chat_iid` for database object ID variables  
- Use `chat` for ChatModel instances
- Be explicit in method parameter names

## Exception Handling Best Practices

### Avoid Broad Exception Handling

- **DO NOT** use bare `except Exception as e:` handlers unless absolutely necessary
- Prefer specific exception types (`ValueError`, `TypeError`, etc.) when possible  
- Let exceptions bubble up to be handled by the framework's error handling system
- This allows for better debugging, error tracking, and crashlytics reporting
- The bot framework handles uncaught exceptions gracefully with user feedback

### When to Use Exception Handling

```python
# ❌ AVOID - Too broad, hides real errors
try:
    result = some_complex_operation()
except Exception as e:
    await message.reply("Something went wrong")
    return

# ✅ PREFER - Specific exceptions only
try:
    user_id = int(user_input)
except ValueError:
    await message.reply(_("Please provide a valid number"))
    return

# ✅ ACCEPTABLE - When you need to catch multiple specific types
try:
    result = await api_call()
except (ConnectionError, TimeoutError) as e:
    await message.reply(_("Service temporarily unavailable"))
    return
```

### Framework Error Handling

The bot framework already provides comprehensive error handling that:
- Logs errors with full stack traces
- Reports errors to monitoring systems
- Provides user-friendly error messages
- Maintains bot stability

Let the framework handle unexpected errors rather than masking them with broad exception handlers.

## Quality Assurance

- All code must pass mypy type checking
- All code must pass flake8 linting
- All code must be formatted with Black
- All user-facing text must be translatable
- All functions must have proper type annotations
- Test coverage should be maintained
- Documentation should be updated for new features
- **Follow chat ID naming conventions strictly**
- **Avoid broad exception handling - prefer specific exceptions**

## Additional Notes

- The project uses GNU AGPLv3 license
- Wiki available at: https://sophie-wiki.orangefox.tech/
- ASS library: https://gitlab.com/SophieBot/ass
- STFU library: https://gitlab.com/SophieBot/stf
- Use MongoDB for persistent data storage
- Use Redis for caching and temporary data
- Follow async/await patterns throughout the codebase
- Prefer composition over inheritance
- Keep functions small and focused on single responsibilities

---

**Remember**: After completing any development task, always run `make commit` to ensure code quality and consistency.

## Feature Flags and Kill Switches

All new medium/high‑risk features, external integrations, and large refactors must be shipped behind a feature flag (aka
kill switch). This allows safe, instant rollbacks without redeploys and enables staged rollouts.

### Implementation Overview

- Storage: Redis hash under key `sophie:kill_switch`
- Runtime API: `sophie_bot/utils/feature_flags.py`
  - `is_enabled(feature: FeatureType) -> bool`
  - `set_enabled(feature: FeatureType, enabled: bool) -> None`
  - `list_all() -> FeatureStates`
- Caching: in‑process cache with ~2s TTL, auto‑refreshed
- Defaults: general features default to enabled; some federation features default to disabled for gradual rollout

File reference:
- `sophie_bot/utils/feature_flags.py` — single source of truth for:
  - `FeatureType` literal union of all flag names
  - `FeatureStates` typed map of flag -> bool
  - `FEATURE_FLAGS` tuple enumeration (order and completeness)
  - `_default_state_map()` default values

### When You MUST Use a Flag

- New user‑facing capabilities (commands, handlers, automations)
- Rewrites/refactors that may affect stability or moderation behavior
- New external services (APIs, storage, schedulers)
- Anything that may need an instant "off" switch in production

### Naming Conventions

- Lower snake_case identifiers, domain‑scoped where useful
- Reuse existing patterns, for example:
  - `ai_chatbot`, `ai_translations`, `ai_moderation`
  - `filters`, `antiflood`
  - `new_feds_*` for federation rollout flags
- Prefer descriptive, durable names. Avoid user or chat‑specific semantics in global flags.

### Adding a New Feature Flag (Required Steps)

1. Edit `sophie_bot/utils/feature_flags.py` and update all of the following:
   - Add the new literal to `FeatureType`
   - Add a `bool` field to `FeatureStates`
   - Append to `FEATURE_FLAGS`
   - Set its default in `_default_state_map()`
2. Choose the default carefully:
   - Kill‑switch for risky changes: default to `True` (enabled) so you can turn it off on incidents
   - Gradual rollout (new area): default to `False` (disabled) until explicitly enabled
3. Run `make commit` to format and type‑check (mypy must pass).

### Using a Flag in Handlers/Services

Handlers (commands, message/callback handlers) must not perform inline feature-flag checks or send "feature disabled" messages. Instead, completely disable handlers via `FeatureFlagFilter` so they never execute when the flag is off.

```python
from __future__ import annotations

from aiogram.handlers import MessageHandler
from aiogram.types import Message
from aiogram import flags

from sophie_bot.filters.feature_flag import FeatureFlagFilter
from sophie_bot.utils.i18n import lazy_gettext as l_


@flags.help(description=l_("AI Chatbot – talk with AI"))
@flags.disableable(name="ai_chat")
class AIChatHandler(MessageHandler):
    @staticmethod
    def filters():
        # Handler will be completely disabled when the flag is off
        return (FeatureFlagFilter("ai_chatbot"),)

    async def handle(self) -> None:  # type: ignore[override]
        message: Message = self.event
        # ... normal handler logic here ...
```

For utility/services functions where a feature toggle selects between old/new behavior within the same API, using `is_enabled` is acceptable. Prefer a fast guard near the entrypoint and avoid user-facing "disabled" messages:

```python
from sophie_bot.utils.feature_flags import is_enabled

async def generate_summary(text: str) -> str:
    if not await is_enabled("ai_translations"):
        return text  # noop when disabled
    # proceed with AI call
```

### Operational Control (Toggling Flags)

You can toggle flags at runtime with either the Python API or Redis CLI. Cache refresh occurs within ~2 seconds.

- Python (admin shell/task):

```python
from sophie_bot.utils.feature_flags import set_enabled

await set_enabled("ai_chatbot", False)
```

- Redis CLI (0/1 values):

```bash
redis-cli HSET sophie:kill_switch ai_chatbot 0
redis-cli HGETALL sophie:kill_switch
```

Notes:
- Treat flags as global to the deployment. They are not per‑chat permissions.
- Do not rely on flags for security. They are operational controls, not auth.

### Testing With Feature Flags

- Prefer black‑box tests that assert behavior both when enabled and disabled.
- Use the public API to flip flags inside tests and restore afterward.

```python
import asyncio
import pytest

from sophie_bot.utils.feature_flags import set_enabled


@pytest.mark.asyncio
async def test_ai_chat_disabled(shutdown_flag: None) -> None:
    await set_enabled("ai_chatbot", False)
    try:
        # call the handler/service and assert the fallback
        ...
    finally:
        await set_enabled("ai_chatbot", True)
```

Tip: when possible, structure your functions so flag checks are isolated and easy to test.

### Common Pitfalls

- Performing inline `is_enabled(...)` checks inside handlers and replying with "feature disabled". Use `FeatureFlagFilter` to disable handlers entirely. 
- Forgetting to add the flag to ALL places in `feature_flags.py` (type union, typed dict, tuple, defaults)
- Surfacing non‑translated user messages when a feature is disabled — always use i18n
- Mixing flag semantics with chat permission logic — keep them separate
- Broad exception handlers masking real failures — follow exception best practices in this guide
