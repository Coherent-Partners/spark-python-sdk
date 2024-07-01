from __future__ import annotations

import math
import random
import re
import uuid
from typing import Any, List, Union, cast

from ._constants import DEFAULT_RETRY_INTERVAL, RETRY_RANDOMIZATION_FACTOR


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
        int(str(value))
        return True
    except ValueError:
        return False


def is_positive_int(value: Any | None) -> bool:
    return is_int(value) and cast(int, value) > 0


def mask(value: str, start: int = 0, end: int = 4, char: str = '*') -> str:
    if not value or start < 0 or end < 0:
        return value
    return value[:start] + char * (len(value) - start - end) + value[-end:]


def sanitize_uri(url: str, leading: bool = False) -> str:
    sanitized = re.sub(r'/{2,}', '/', url)
    sanitized = sanitized.rstrip('/')
    return sanitized if leading else sanitized.lstrip('/')


def find_value_from_dict(key_path: str, data: dict, default: Any = None) -> Any:
    """
    Walks through a nested dictionary-based dataset and returns the value associated
    with the key path.
    """
    if not isinstance(data, dict):
        return default
    try:
        keys = key_path.split('.')
    except AttributeError:
        return default
    if not keys:
        return default

    # safe operations
    value = data.copy()
    for k in keys:
        value = cast(dict, value.get(k))
    return value


def get_retry_timeout(retries: int, interval=DEFAULT_RETRY_INTERVAL) -> float:
    randomization = random.uniform(0, 1) * RETRY_RANDOMIZATION_FACTOR
    return math.pow(2, retries) * interval * randomization


def join_list_str(value: Union[None, str, List[str]] = None, sep: str = ',') -> Union[str, None]:
    return sep.join(value) if isinstance(value, list) else value


def is_not_empty_list(value: Any | None) -> bool:
    return isinstance(value, list) and len(value) > 0


def get_uuid() -> str:
    return str(uuid.uuid4())
