# PyKorone Coding Guidelines

We are building a Python project using Hydrogram (a Pyrogram fork) for Telegram bot development. When generating or suggesting code, follow these guidelines:

1. Use latest Python features appropriately:
   - Type hints with the latest typing module features
   - Pattern matching and structural pattern matching
   - F-strings for all string formatting
   - Walrus operator (:=) when it improves readability
   - And all other latest Python features

2. Follow PEP 8 style guidelines:
   - 4 spaces for indentation
   - Maximum line length of 99 characters
   - snake_case for functions and variables
   - PascalCase for classes
   - UPPER_CASE for constants
   - Use positional arguments for logging statements instead of f-strings
   - Code style consistency using Ruff.

3. Project architecture:
   - Keep functions small and focused on a single responsibility
   - Use type hints consistently on all functions and methods
   - Prefer nheritance over composition when appropriate
   - Use async/await for all I/O operations
   - Use context managers for file and resource management
   - Use async context managers for async I/O operations

4. Code organization:
   - Organize code into modules and packages
   - Use relative imports within the package
   - Follow a consistent naming pattern for handler functions

5. Error handling:
   - Use try/except blocks around external API calls
   - Log errors with appropriate context
   - Provide user-friendly error messages

6. Documentation:
    - Use docstrings for all public functions, methods and classes
    - Include type hints in docstrings
    - Use Google-style docstrings format
