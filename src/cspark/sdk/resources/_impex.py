from typing import Optional, Union

from .._config import Config
from ._base import ApiResource, Uri, UriParams

__all__ = ['Wasm', 'Files']


class Wasm(ApiResource):
    def __init__(self, config: Config):
        super().__init__(config)

    def download(
        self,
        uri: Union[None, str, UriParams] = None,
        *,
        folder: Optional[str] = None,
        service: Optional[str] = None,
        service_id: Optional[str] = None,
        version_id: Optional[str] = None,
        public: Optional[bool] = False,
    ):
        params = (
            UriParams(folder, service, service_id, version_id=version_id, public=public)
            if uri is None
            else Uri.to_params(uri)
        )
        service_uri = Uri.validate(params).encode()
        endpoint = f'getnodegenzipbyId/{service_uri}'
        resource = 'nodegen' + ('/public' if params.public else '')
        url = Uri.partial(resource, base_url=self.config.base_url.full, endpoint=endpoint)

        return self.request(url)


class Files(ApiResource):
    def __init__(self, config: Config):
        super().__init__(config)

    def download(self, url: str):
        return self.request(url)
