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
    if "%%%" not in text:
        return text

    parts = text.split("%%%")
    result = []

    i = 0
    while i < len(parts):
        # Non-delimited part, keep as-is
        result.append(parts[i])

        # Delimited segment follows if not at the end
        if i + 1 < len(parts):
            options = []
            # Gather delimited options until next regular part or end
            j = i + 1
            while j < len(parts) and parts[j].strip() == "":
                # Skip empty segments (consecutive delimiters)
                j += 1
            if j < len(parts):
                options.append(parts[j])
                j += 1
            while j < len(parts) and parts[j].strip() != "":
                options.append(parts[j])
                j += 1
            if options:
                selected_option = choice([opt for opt in options if opt.strip() != ""])
                result.append(selected_option)
            i = j - 1  # adjust the index to right position
        i += 1

    return "".join(result).rstrip()
