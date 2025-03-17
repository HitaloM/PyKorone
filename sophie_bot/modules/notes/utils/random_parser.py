from random import choice


def parse_random_text(text: str) -> str:
    """
    Process text by keeping non-delimited parts intact and randomly selecting from delimited parts.

    - Regular text is preserved as is
    - When %%% delimiters are found, one of the options separated by them is randomly chosen
    - Supports multi-line delimiters and options

    Example:
    Input: "Hello\n%%%\nworld\n%%%\nuniverse\n%%%\n"
    Output: "Hello\nworld"
    """
    # If no delimiters, return the text as is
    if "%%%" not in text:
        return text

    result = []
    parts = text.split("%%%")

    for i in range(0, len(parts), 2):
        # Add non-delimited parts
        if parts[i].strip():
            result.append(parts[i])

        # Handle random selection for delimited parts
        if i + 1 < len(parts):
            # Split and strip options, keeping whitespace (including newlines)
            options = [opt for opt in parts[i + 1].split('%%%') if opt.strip()]
            if options:
                result.append(choice(options))

    return ''.join(result)
