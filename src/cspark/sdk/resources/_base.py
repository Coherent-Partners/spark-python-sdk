import logging
import uuid
from typing import Mapping, Optional

import httpx

from .._config import Config
from .._version import about as sdk_info
from .._version import sdk_ua_header

__all__ = ['ApiResource']


class ApiResource:
    def __init__(self, config: Config):
        self.config = config
        self._client = httpx.Client()

        logging.basicConfig(
            format='[%(name)s] %(asctime)s [%(levelname)s] - %(message)s',
            datefmt='%m/%d/%Y, %H:%M:%S %p',
            level=logging.INFO,
        )
        # FIXME: Redefine HTTP handler to use the SDK config instead of httpx's.
        self.logger = logging.getLogger()

    @property
    def default_headers(self):
        return {
            **self.config.extra_headers,
            'User-Agent': sdk_info,
            'x-spark-ua': sdk_ua_header,
            'x-request-id': uuid.uuid4().hex,
            'x-tenant-name': self.config.base_url.tenant,
        }

    def request(
        self,
        url: str,
        *,
        method: str = 'GET',
        headers: Mapping[str, str] = {},
        params: Optional[Mapping[str, str]] = None,
        data=None,
        files=None,
    ):
        request = self._client.build_request(
            method,
            url,
            params=params,
            headers={
                **headers,
                **self.default_headers,
            },
            data=data,
            files=files,
            timeout=self.config.timeout / 1000,
        )

        self.logger.debug(f'{method} {url}')
        return self._client.send(request)

    def close(self):
        self._client.close()
