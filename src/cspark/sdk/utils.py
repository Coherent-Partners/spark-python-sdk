from typing import Any, cast


def is_str(value: Any | None) -> bool:
    return isinstance(value, str)


def is_str_empty(value: Any | None) -> bool:
    return value is None or (isinstance(value, str) and value.strip() == '')


def is_str_not_empty(value: Any | None) -> bool:
    return isinstance(value, str) and value.strip() != ''


def is_int(value: Any | None) -> bool:
    if isinstance(value, int):
        return True
    try:
        int(cast(int, value))
        return True
    except ValueError:
        return False


def is_positive_int(value: Any | None) -> bool:
    return is_int(value) and cast(int, value) > 0
