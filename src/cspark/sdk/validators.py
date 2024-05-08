import re
from typing import List

from .errors import SparkError
from .utils import is_positive_int, is_str_empty

__all__ = ['Validators']


class BaseValidator:
    _errors: List[SparkError] = []

    @property
    def errors(self):
        return self._errors

    def reset(self):
        self._errors.clear()


class EmptyStringValidator(BaseValidator):
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(EmptyStringValidator, cls).__new__(cls)
        cls.instance.reset()
        return cls.instance

    def validate(self, value: str | None, message: str | None = None):
        if is_str_empty(value):
            raise SparkError.sdk(message or 'must be non-empty string value', cause=value)

    def is_valid(self, value: str | None, message: str | None = None) -> bool:
        try:
            self.validate(value, message)
            return True
        except SparkError as error:
            self._errors.append(error)
            return False


class PositiveIntegerValidator(BaseValidator):
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(PositiveIntegerValidator, cls).__new__(cls)
        cls.instance.reset()
        return cls.instance

    def validate(self, value: int | None):
        if not is_positive_int(value):
            raise SparkError.sdk('must be a positive integer', value)

    def is_valid(self, value: int | None) -> bool:
        try:
            self.validate(value)
            return True
        except SparkError as error:
            self._errors.append(error)
            return False


class BaseUrlValidator(BaseValidator):
    _wildcard = re.compile(r'^https?://(?:[^./]+\.)+coherent\.global(?:/[^/?#]+)*(?:[?#].*)?$', re.IGNORECASE)

    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(BaseUrlValidator, cls).__new__(cls)
        cls.instance.reset()
        return cls.instance

    def validate(self, value: str | None):
        if value is None or str(value).strip() == '':  # FIXME: use utils when available
            raise SparkError.sdk('base URL is required', value)

        if not self._wildcard.match(value):
            raise SparkError.sdk('must be a Spark base URL <*.coherent.global>', value)

    def is_valid(self, value: str | None) -> bool:
        try:
            self.validate(value)
            return True
        except SparkError as error:
            self._errors.append(error)
            return False


class Validators:
    empty_str = EmptyStringValidator
    positive_int = PositiveIntegerValidator
    base_url = BaseUrlValidator
