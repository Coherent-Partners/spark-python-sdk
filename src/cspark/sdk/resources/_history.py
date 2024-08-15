from typing import Optional, Union, cast

from .._config import Config
from .._errors import SparkError
from .._utils import is_int, is_str_empty
from ._base import ApiResource, Uri, UriParams

__all__ = ['History']


class History(ApiResource):
    def __init__(self, config: Config):
        super().__init__(config)

    def rehydrate(
        self,
        uri: Union[None, str, UriParams],
        *,
        call_id: str,
        folder: Optional[str] = None,
        service: Optional[str] = None,
        index: Optional[int] = None,
    ):
        if is_str_empty(call_id):
            raise SparkError.sdk('call_id is required when rehydrating', {'call_id': call_id})

        uri = Uri.validate(UriParams(folder, service) if uri is None else Uri.to_params(uri))
        url = Uri.of(uri.pick('folder', 'service'), base_url=self.config.base_url.full, endpoint=f'download/{call_id}')
        params = {'index': str(index)} if is_int(index) and cast(int, index) >= 0 else None
        response = self.request(url, params=params)

        if isinstance(response.data, dict) and isinstance(response.data['response_data'], dict):
            download_url = response.data['response_data']['download_url']
            response.data['status'] = 'Success'  # comes as None from the API
        else:
            raise SparkError('failed to produce a download URL', response)

        return self.request(download_url).copy_with(data=response.data)
