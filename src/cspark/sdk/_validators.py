import re
from abc import ABC, abstractmethod
from json import loads
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


class TransformValidator(BaseValidator):
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(TransformValidator, cls).__new__(cls)
        cls.instance.reset()
        return cls.instance

    def validate(self, value: str):
        if not value:
            raise SparkError.sdk('must be a properly defined JSON object', value)

        try:
            json_data = loads(value)
        except Exception as cause:
            raise SparkError.sdk(f'<{value}> must be a valid JSON object', cause) from cause

        if not json_data.get('transform_type'):
            raise SparkError.sdk("JSON object must have a 'transform_type' property", value)

        target_version = json_data.get('target_api_version')
        if not target_version or target_version not in ['v3', 'v4']:
            raise SparkError.sdk("'target_api_version' must be either 'v3' or 'v4'", value)


class Validators:
    empty_str = EmptyStringValidator
    positive_num = PositiveNumberValidator
    base_url = BaseUrlValidator
    transform = TransformValidator
