# Regex

Explore and test regular expressions or correct errors in messages within a group chat.

## Commands

- `s/regex/replacement/flags`: This command replaces occurrences of "regex" with "replacement" from the replied message. Flags are optional and modify the behavior of the search and replace operation.

```{admonition} **Supported Flags**:
:class: seealso

- `i`: Performs case-insensitive matching.
- `m`: Allows the `^` and `$` to match the start and end of each line (not just the start and end of the string).
- `s`: Enables the dot `.` to match newline characters.
- `g`: Applies the replacement globally across all matches, not just the first.
- `x`: Allows for spaces and comments in the pattern for more readable regex.
```

### Examples

- `s/Hello/Hi/`
  This command replaces the first occurrence of "Hello" with "Hi".

- `s/Hello/Hi/g`
  This replaces all occurrences of "Hello" with "Hi".

- `s/Hello/Hi/gi`
  This performs a global, case-insensitive replacement of "Hello" with "Hi".

- `s/Hello/Hi/gim`
  This command replaces "Hello" with "Hi" globally, with case-insensitivity, and across multiple lines.
