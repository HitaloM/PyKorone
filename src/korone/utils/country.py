_REGIONAL_INDICATOR_A = 0x1F1E6
_ASCII_A = ord("A")


def country_flag(country_code: str) -> str:
    code = country_code.strip()
    if len(code) != 2 or not code.isascii() or not code.isalpha():
        return ""

    code = code.upper()
    return "".join(chr(_REGIONAL_INDICATOR_A + ord(character) - _ASCII_A) for character in code)
