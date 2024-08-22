import re

MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 100

SPECIAL_CHARS = "@$!%*?&_#"


def has_cyrillic(text: str) -> bool:
    # We use cyrillic range: [\u0400-\u04FF]
    return bool(re.search("[\u0400-\u04FF]", text))


def has_latin(text: str) -> bool:
    return bool(re.search("[a-zA-Z]", text))


def is_cyrillic(text: str) -> bool:
    return has_cyrillic(text) and not has_latin(text)


def is_latin(text: str) -> bool:
    return has_latin(text) and not has_cyrillic(text)


def is_strong_password(password: str) -> bool:
    if MIN_PASSWORD_LENGTH > len(password) > MAX_PASSWORD_LENGTH:
        return False

    has_lowercase = False
    has_uppercase = False
    has_digit = False
    has_special_char = False

    for char in password:
        if char.islower():
            has_lowercase = True
        elif char.isupper():
            has_uppercase = True
        elif char.isdigit():
            has_digit = True
        elif char in SPECIAL_CHARS:
            has_special_char = True

    return has_lowercase and has_uppercase and has_digit and has_special_char
