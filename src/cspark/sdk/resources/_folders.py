from datetime import datetime
from typing import Any, BinaryIO, Optional, Union

from .._config import Config
from .._constants import SPARK_SDK
from .._errors import SparkApiError, SparkError
from .._utils import DateUtils, get_uuid
from ._base import ApiResource, Uri

__all__ = ['Folders']


class Folders(ApiResource):
    def __init__(self, config: Config):
        super().__init__(config)
        self._base_uri = {'base_url': self.config.base_url.value, 'version': 'api/v1'}

    @property
    def categories(self) -> 'Categories':
        return Categories(self.config)

    def find(
        self,
        name: Optional[str] = None,
        *,
        favorite: Optional[bool] = None,
        page: int = 1,
        size: int = 100,
        sort: str = '-updated',
        **params: Any,
    ):
        url = Uri.of(None, endpoint='product/list', **self._base_uri)
        search = [{'field': k, 'value': v} for k, v in {**params, 'name': name, 'isstarred': favorite}.items() if v]
        body = {'search': search, 'page': page, 'pageSize': size, 'sort': sort}
        body.update({'shouldFetchActiveServicesCount': True})

        return self.request(url, method='POST', body=body)

    def create(
        self,
        name: str,
        *,
        description: Optional[str] = None,
        category: Optional[str] = None,
        start_date: Union[None, str, int, datetime] = None,
        launch_date: Union[None, str, int, datetime] = None,
        status: Optional[str] = None,
        cover: Optional[BinaryIO] = None,
    ):
        url = Uri.of(None, endpoint='product/create', **self._base_uri)
        startdate, launchdate = DateUtils.parse(start_date, launch_date)
        form = {
            'Name': name,
            'Description': description or f'Created by {SPARK_SDK}',
            'Category': category or 'Other',
            'StartDate': startdate.isoformat(),
            'LaunchDate': launchdate.isoformat(),
            'Status': status or 'Design',
        }
        response = self.request(url, method='POST', form=form)

        if response.status == 200 and isinstance(response.data, dict) and response.data['status'] == 'Success':
            if cover:
                self.upload_cover(response.data['data']['folderId'], cover)
            return self.request(response.data['data']['get_product_url'])

        cause = SparkApiError.to_cause(request=response.raw_request, response=response.raw_response)
        if response.data['errorCode'] == 'PRODUCT_ALREADY_EXISTS':  # type: ignore
            error = SparkError.api(409, {'message': f'folder name <{name}> already exists', 'cause': cause})
        else:
            error = SparkError.api(response.status, {'message': f'failed to create folder <{name}>', 'cause': cause})
        self.logger.error(error.message)
        raise error

    def update(
        self,
        id: str,
        *,
        description: Optional[str] = None,
        category: Optional[str] = None,
        start_date: Union[None, str, int, datetime] = None,
        launch_date: Union[None, str, int, datetime] = None,
        cover: Optional[BinaryIO] = None,
    ):
        url = Uri.of(None, endpoint=f'product/update/{id}', **self._base_uri)
        if cover:
            self.upload_cover(id, cover)

        body: dict[str, Any] = {'shouldTrackUserAction': True}
        if description:
            body['description'] = description
        if category:
            body['category'] = category
        if DateUtils.is_date(start_date):
            body['startDate'] = DateUtils.to_datetime(start_date).isoformat()  # type: ignore
        if DateUtils.is_date(launch_date):
            body['launchDate'] = DateUtils.to_datetime(launch_date).isoformat()  # type: ignore
        return self.request(url, method='POST', body=body)

    def delete(self, id: str):
        url = Uri.of(None, endpoint=f'product/delete/{id}', **self._base_uri)
        self.logger.warning('deleting folder will also delete all its services')

        return self.request(url, method='DELETE')

    def upload_cover(self, id: str, image: BinaryIO, filename: Optional[str] = None):
        url = Uri.of(None, endpoint='product/uploadcoverimage', **self._base_uri)
        files = {'coverImage': filename and (filename, image) or image}

        return self.request(url, method='POST', form={'id': id}, files=files)


class Categories(ApiResource):
    def __init__(self, config: Config):
        super().__init__(config)
        self._base_uri = {'base_url': self.config.base_url.value, 'version': 'api/v1'}

    def list(self):
        return self.request(Uri.of(None, endpoint='lookup/getcategories', **self._base_uri))

    def save(self, name: str, *, key: Optional[str] = None, icon: Optional[str] = None):
        url = Uri.of(None, endpoint='lookup/savecategory', **self._base_uri)
        body = {'value': name, 'key': key or get_uuid(), 'icon': icon or 'other.svg'}
        response = self.request(url, method='POST', body=body)
        return response.copy_with(data=self.__extract_data(response.data))

    def delete(self, key: str):
        url = Uri.of(None, endpoint=f'lookup/deletecategory/{key}', **self._base_uri)
        response = self.request(url, method='DELETE')
        return response.copy_with(data=self.__extract_data(response.data))

    def __extract_data(self, data: Any):
        if not isinstance(data, dict):
            return data

        categories = data.get('data', {}).get('Metadata.ProductCategories', [])
        return [{k.lower(): v for k, v in c.items()} for c in categories]
