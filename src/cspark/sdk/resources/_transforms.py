from dataclasses import dataclass
from json import dumps, loads
from typing import Any, List, Optional, Union

from .._config import Config
from .._errors import SparkError
from .._validators import Validators
from ._base import ApiResource, Uri

__all__ = ['Transforms', 'Transform']


@dataclass(frozen=True)
class Transform:
    schema: Optional[str] = None
    api_version: Optional[str] = None
    inputs: Optional[str] = None
    outputs: Optional[str] = None


@dataclass(frozen=True)
class TransformParams:
    folder: Optional[str] = None
    name: Optional[str] = None

    def validate(self) -> None:
        if not self.folder or not self.name:
            raise SparkError.sdk('transform folder and name are required', self.__dict__)

    def to_uri(self) -> str:
        self.validate()
        return f'{self.folder}/{self.name}'


class Transforms(ApiResource):
    def __init__(self, config: Config):
        super().__init__(config)
        self._base_uri = {'base_url': self.config.base_url.full, 'version': 'api/v4'}

    def list(
        self,
        folder: str,
        *,
        page: int = 1,
        size: int = 100,
        sort: str = '-updatedAt',
        search: Optional[List[Any]] = None,
    ):
        url = Uri.of(None, endpoint=f'transform/list/{folder}', **self._base_uri)
        request_data = {'page': page, 'pageSize': size, 'sort': sort, 'search': search or []}

        return self.request(url, method='POST', body={'request_data': request_data})

    def validate(self, transform: Union[str, Transform]):
        url = Uri.of(None, endpoint=f'transform/validation', **self._base_uri)
        body = {'transform_content': self.__build(transform)}

        return self.request(url, method='POST', body=body)

    def get(self, uri: Optional[str] = None, *, folder: Optional[str] = None, name: Optional[str] = None):
        endpoint = f'transform/{uri or TransformParams(folder, name).to_uri()}'
        url = Uri.of(None, endpoint=endpoint, **self._base_uri)

        return self.request(url, method='GET')

    def save(self, *, folder: str, name: str, transform: Union[str, Transform]):
        url = Uri.of(None, endpoint=f'transform/{folder}/{name}', **self._base_uri)
        body = {'transform_content': self.__build(transform)}

        return self.request(url, method='POST', body=body)

    def delete(self, uri: Optional[str] = None, *, folder: Optional[str] = None, name: Optional[str] = None):
        endpoint = f'transform/{uri or TransformParams(folder, name).to_uri()}'
        url = Uri.of(None, endpoint=endpoint, **self._base_uri)

        return self.request(url, method='DELETE')

    def __build(self, value: Union[str, Transform]) -> str:
        value = Transform(**loads(value)) if isinstance(value, str) else value

        if value.schema and 'nodejs22' in value.schema.lower():
            return dumps({'transform_type': value.schema, 'transform_code': value.inputs})

        transform = dumps(
            {
                'transform_type': value.schema or 'JSONtransforms_v1.0.1',
                'target_api_version': value.api_version or 'v3',
                'input_body_transform': value.inputs,
                'output_body_transform': value.outputs,
            }
        )
        Validators.transform().validate(transform)

        return transform
