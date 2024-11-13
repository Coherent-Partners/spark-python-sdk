from __future__ import annotations

import math
import random
import re
import uuid
from datetime import datetime, timedelta
from typing import Any, List, Optional, Tuple, Union, cast

from ._constants import DEFAULT_RETRY_INTERVAL, RETRY_RANDOMIZATION_FACTOR


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


def sanitize_uri(url: str, leading: bool = False) -> str:
    sanitized = re.sub(r'/{2,}', '/', url)
    sanitized = sanitized.rstrip('/')
    return sanitized if leading else sanitized.lstrip('/')


def find_value_from_dict(key_path: str, data: dict, default: Any = None) -> Any:
    """
    Walks through a nested dictionary-based dataset and returns the value associated
    with the key path.
    """
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


def get_retry_timeout(retries: int, interval: float = DEFAULT_RETRY_INTERVAL) -> float:
    randomization = random.uniform(0, 1) * RETRY_RANDOMIZATION_FACTOR
    return math.pow(2, retries) * interval * randomization


def is_not_empty_list(value: Any | None) -> bool:
    return isinstance(value, list) and len(value) > 0


def get_uuid() -> str:
    return str(uuid.uuid4())


class StringUtils:
    @staticmethod
    def is_str(value: Any | None) -> bool:
        return isinstance(value, str)

    @staticmethod
    def is_empty(value: Any | None) -> bool:
        return value is None or (isinstance(value, str) and value.strip() == '')

    @staticmethod
    def is_not_empty(value: Any | None) -> bool:
        return isinstance(value, str) and value.strip() != ''

    @staticmethod
    def mask(value: str, start: int = 0, end: int = 4, char: str = '*') -> str:
        if not value or start < 0 or end < 0:
            return value
        return value[:start] + char * (len(value) - start - end) + value[-end:]

    @staticmethod
    def join(value: Union[None, str, List[str]] = None, sep: str = ',') -> Union[str, None]:
        return sep.join(value) if isinstance(value, list) else value


class DateUtils:
    @staticmethod
    def is_date(value: Optional[int | str | datetime]) -> bool:
        if isinstance(value, datetime):
            return True
        if isinstance(value, (str, int)):
            try:
                if isinstance(value, int):
                    datetime.fromtimestamp(value / 1000)  # Treat value as a Unix timestamp in milliseconds.
                else:
                    datetime.fromisoformat(value)  # Handles ISO strings like "YYYY-MM-DD"
                return True
            except ValueError:
                return False
        return False

    @staticmethod
    def parse(
        start: Optional[int | str | datetime] = None,
        end: Optional[int | str | datetime] = None,
        *,
        years: int = 10,
        months: int = 0,
        days: int = 0,
    ) -> Tuple[datetime, datetime]:
        start_date = DateUtils.to_datetime(start) if start else datetime.now()

        # Calculate the end date
        if end and DateUtils.is_after(end, start_date):
            end_date = DateUtils.to_datetime(end)
        else:
            # Handling months overflow manually
            year = start_date.year + years
            month = start_date.month + months
            day = start_date.day + days

            while month > 12:
                month -= 12
                year += 1

            end_date = start_date.replace(year=year, month=month) + timedelta(days=day)

        return start_date, end_date

    @staticmethod
    def is_before(date: Union[str, int, datetime], when: datetime) -> bool:
        return DateUtils.to_datetime(date) < when

    @staticmethod
    def is_after(date: Union[str, int, datetime], when: datetime) -> bool:
        return DateUtils.to_datetime(date) > when

    @staticmethod
    def to_datetime(value: Union[str, int, datetime]) -> datetime:
        if isinstance(value, datetime):
            return value
        if isinstance(value, int):
            return datetime.fromtimestamp(value / 1000)  # Unix timestamp in milliseconds
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                return datetime.strptime(value, '%Y-%m-%d')
