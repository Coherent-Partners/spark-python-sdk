from typing import Any, List, Optional, Union

from .._base import Uri
from .._transforms import Transform, TransformParams, build_transform
from ._base import AsyncApiResource

__all__ = ['AsyncTransforms']


class AsyncTransforms(AsyncApiResource):
    @property
    def base_uri(self) -> dict[str, str]:
        return {'base_url': self.config.base_url.full, 'version': 'api/v4'}

    async def list(
        self,
        folder: str,
        *,
        page: int = 1,
        size: int = 100,
        sort: str = '-updatedAt',
        search: Optional[List[Any]] = None,
    ):
        url = Uri.of(None, endpoint=f'transform/list/{folder}', **self.base_uri)
        request_data = {'page': page, 'pageSize': size, 'sort': sort, 'search': search or []}

        return await self.request(url, method='POST', body={'request_data': request_data})

    async def validate(self, transform: Union[str, Transform]):
        url = Uri.of(None, endpoint=f'transform/validation', **self.base_uri)
        body = {'transform_content': build_transform(transform)}

        return await self.request(url, method='POST', body=body)

    async def get(self, uri: Optional[str] = None, *, folder: Optional[str] = None, name: Optional[str] = None):
        endpoint = f'transform/{uri or TransformParams(folder, name).to_uri()}'
        url = Uri.of(None, endpoint=endpoint, **self.base_uri)

        return await self.request(url, method='GET')

    async def save(self, *, folder: str, name: str, transform: Union[str, Transform]):
        url = Uri.of(None, endpoint=f'transform/{folder}/{name}', **self.base_uri)
        body = {'transform_content': build_transform(transform)}

        return await self.request(url, method='POST', body=body)

    async def delete(self, uri: Optional[str] = None, *, folder: Optional[str] = None, name: Optional[str] = None):
        endpoint = f'transform/{uri or TransformParams(folder, name).to_uri()}'
        url = Uri.of(None, endpoint=endpoint, **self.base_uri)

        return await self.request(url, method='DELETE')
