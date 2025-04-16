import re
from abc import ABC, abstractmethod
from typing import List, Optional, Union

from ._errors import SparkError
from ._utils import StringUtils, is_positive_int

__all__ = ['Validators']


class BaseValidator(ABC):
    _errors: List[SparkError] = []

    @property
    def errors(self):
        return self._errors

    @abstractmethod
    def validate(self, *args, **kwargs):
        raise NotImplementedError

    def is_valid(self, *args, **kwargs) -> bool:
        try:
            self.validate(*args, **kwargs)
            return True
        except SparkError as error:
            self._errors.append(error)
            return False

    def reset(self):
        self._errors.clear()


class EmptyStringValidator(BaseValidator):
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(EmptyStringValidator, cls).__new__(cls)
        cls.instance.reset()
        return cls.instance

    def validate(self, value: Optional[str], message: Optional[str] = None):
        if StringUtils.is_empty(value):
            raise SparkError.sdk(message or 'must be non-empty string value', cause=value)


class PositiveNumberValidator(BaseValidator):
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(PositiveNumberValidator, cls).__new__(cls)
        cls.instance.reset()
        return cls.instance

    def validate(self, value: Union[None, int, float]):
        if not is_positive_int(value):
            raise SparkError.sdk('must be a positive number', value)


class BaseUrlValidator(BaseValidator):
    _wildcard = re.compile(r'^https://(?:[^./]+\.)+coherent\.global(?:/[^/?#]+)*(?:[?#].*)?$', re.IGNORECASE)

    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(BaseUrlValidator, cls).__new__(cls)
        cls.instance.reset()
        return cls.instance

    def validate(self, value: Optional[str]):
        if StringUtils.is_empty(value):
            raise SparkError.sdk('base URL is required', value)

        if not self._wildcard.match(str(value).rstrip('/')):
            raise SparkError.sdk('must be a Spark base URL <*.coherent.global>', value)


class Validators:
    empty_str = EmptyStringValidator
    positive_num = PositiveNumberValidator
    base_url = BaseUrlValidator
