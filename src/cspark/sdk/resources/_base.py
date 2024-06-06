import logging
import re
import uuid
from dataclasses import dataclass
from typing import Mapping, Optional, Union

from httpx import URL, Client

from .._config import Config
from .._errors import SparkError
from .._utils import is_str_empty, sanitize_uri
from .._version import about as sdk_info
from .._version import sdk_ua_header

__all__ = ['ApiResource', 'UriParams', 'Uri']


class ApiResource:
    def __init__(self, config: Config):
        self.config = config
        self._client = Client()

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
            # TODO: use httpx.Auth instead (https://www.python-httpx.org/advanced/authentication/)
            # httpx comes with auth flow for different auth schemes.
            **self.config.auth.as_header,
        }

    def request(
        self,
        url: Union[str, 'Uri'],
        *,
        method: str = 'GET',
        headers: Mapping[str, str] = {},
        params: Optional[Mapping[str, str]] = None,
        body=None,
        files=None,
    ):
        request = self._client.build_request(
            method,
            url.value if isinstance(url, Uri) else url,
            params=params,
            headers={**headers, **self.default_headers},
            json=body,
            files=files,
            timeout=self.config.timeout / 1000,
        )

        self.logger.debug(f'{method} {url}')
        return self._client.send(request)

    def close(self):
        self._client.close()


@dataclass(frozen=True)
class UriParams:
    folder: Optional[str] = None
    service: Optional[str] = None
    service_id: Optional[str] = None
    version: Optional[str] = None
    version_id: Optional[str] = None
    proxy: Optional[str] = None
    public: Optional[bool] = False


class Uri:
    def __init__(self, url: URL):
        self._url = url

    @property
    def value(self) -> str:
        return str(self._url)

    @staticmethod
    def of(
        uri: Optional[UriParams] = None,
        *,
        base_url: str = '',
        version: str = 'api/v3',
        endpoint: str = '',
    ) -> 'Uri':
        uri = uri or UriParams()
        path = version
        if uri.public:
            path += '/public'

        if uri.folder and uri.service:
            path += f'/folders/{uri.folder}/services/{uri.service}'
        elif uri.version_id:
            path += f'/version/{uri.version_id}'
        elif uri.proxy:
            path += f'/proxy/{sanitize_uri(uri.proxy)}'

        if endpoint and not uri.proxy:
            path += f'/{endpoint}'

        try:
            return Uri(URL(f'{base_url}/{path}'))
        except Exception as cause:
            raise SparkError.sdk('invalid URI params', uri) from cause

    @staticmethod
    def partial(
        resource: str,
        *,
        base_url: str = '',
        version: str = 'api/v3',
        endpoint: str = '',
    ) -> 'Uri':
        try:
            resource = sanitize_uri(resource)
            if version:
                resource = f'{version}/{resource}'
            if endpoint:
                resource += f'/{endpoint}'
            resource = f'{base_url}/{resource}'

            return Uri(URL(resource))
        except Exception as cause:
            if isinstance(cause, SparkError):
                raise SparkError.sdk(f'invalid service URI <{resource}>', cause) from cause
            raise SparkError(f'failed to build Spark endpoint from <{resource}>', cause) from cause

    @staticmethod
    def to_params(uri: Union[str, UriParams]) -> UriParams:
        return Uri.decode(uri) if isinstance(uri, str) else uri

    @staticmethod
    def decode(uri: str) -> UriParams:
        uri = re.sub('folders/', '', sanitize_uri(uri))
        uri = re.sub('services/', '', uri)
        match = re.match(r'^([^\/]+)\/([^[]+)(?:\[(.*?)\])?$', uri)
        if match:
            folder, service, version = match.groups()
            if folder == 'version':
                return UriParams(version_id=service)
            if folder == 'service':
                return UriParams(service_id=service)
            version = None if is_str_empty(version) else version
            return UriParams(folder=folder, service=service, version=version)
        return UriParams()

    @staticmethod
    def encode(uri: UriParams, long: bool = True) -> str:
        folder, service, version = uri.folder, uri.service, uri.version
        if uri.version_id:
            return f'version/{uri.version_id}'
        if uri.service_id:
            return f'service/{uri.service_id}'
        if folder and service:
            if long:
                return f'folders/{folder}/services/{service}{f"[{version}]" if version else ""}'
            return f'{folder}/{service}{f"[{version}]" if version else ""}'
        return ''

    def __str__(self) -> str:
        return self.value
