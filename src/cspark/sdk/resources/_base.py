from __future__ import annotations

import re
import time
from dataclasses import dataclass
from types import TracebackType
from typing import Any, Mapping, Optional, Union

from httpx import URL, Client, Headers, HTTPError, HTTPStatusError, Request, RequestError, Response

from .._config import Config
from .._errors import SparkApiError, SparkError
from .._logger import get_logger
from .._utils import StringUtils, get_retry_timeout, get_uuid, sanitize_uri
from .._version import about, sdk_ua_header

__all__ = ['ApiResource', 'UriParams', 'Uri', 'HttpResponse']


class ApiResource:
    def __init__(self, config: Config):
        self.config = config
        self.logger = get_logger(**config.logger.__dict__)
        self._client = config.http_client or Client(timeout=config.timeout / 1000)

    def __enter__(self):
        return self

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        # Ideally, let users handle the closing of the custom HTTP client.
        if self.config.http_client:
            return
        self.close()

    def close(self):
        if not self._client.is_closed:
            self._client.close()

    @property
    def default_headers(self):
        return {
            **self.config.extra_headers,
            'User-Agent': about,
            'x-spark-ua': sdk_ua_header,
            'x-request-id': get_uuid(),
            'x-tenant-name': self.config.base_url.tenant,
        }

    def request(
        self,
        url: Union[str, 'Uri', URL],
        *,
        method: str = 'GET',
        headers: Mapping[str, str] = {},
        params: Optional[Mapping[str, str]] = None,
        body: Optional[Any] = None,
        content: Optional[bytes] = None,
        form=None,
        files=None,
    ) -> 'HttpResponse':
        url = str(url)
        request = self._client.build_request(
            method,
            url,
            params=params,
            headers={**headers, **self.default_headers},
            data=form,
            json=body,
            content=content,
            files=files,
        )

        self.logger.debug(f'{method} {url}')
        return self.__fetch(request)

    def __fetch(self, request: Request, retries: int = 0) -> 'HttpResponse':
        request.headers.update(self.config.auth.as_header)

        response, status_code = None, 0
        err_msg = f'an error occurred while fetching <{request.url}>'

        try:
            response = self._client.send(request)
            response.raise_for_status()
        except RequestError as err:
            err_msg += f'; {err}'  # occurs while issuing a request; hence no response
            raise SparkError.sdk(err_msg, SparkApiError.no_response(request)) from err
        except HTTPStatusError as err:
            err_msg = str(err)
        except HTTPError as err:
            err_msg += f'; {err}'
        except Exception:
            pass  # possibly runtime error but should not interrupt this flow

        if not response:
            raise SparkError.sdk(err_msg, SparkApiError.no_response(request))

        status_code = response.status_code
        if status_code >= 400:
            if status_code == 401 and self.config.auth.type == 'oauth' and retries < self.config.max_retries:
                self.config.auth.oauth.retrieve_token(self.config)  # pyright: ignore[reportOptionalMemberAccess]
                return self.__fetch(request, retries + 1)

            if (status_code == 408 or status_code == 429) and retries < self.config.max_retries:
                self.logger.debug(f'retrying request due to status code {status_code}...')
                delay = get_retry_timeout(retries, self.config.retry_interval)
                time.sleep(delay)
                return self.__fetch(request, retries + 1)

            raise SparkError.api(
                status_code,
                {'message': f'failed to fetch <{request.url}>', 'cause': SparkApiError.to_cause(request, response)},
            )

        # otherwise, ok response
        ok_response = {
            'status': status_code,
            'data': None,
            'buffer': response.content,
            'headers': response.headers,
            'raw_request': request,
            'raw_response': response,
        }

        content_type = response.headers.get('content-type', '')
        if 'application/json' in content_type:
            try:
                ok_response['data'] = response.json()
            except Exception:
                ok_response['data'] = response.text
        return HttpResponse(**ok_response)


def download(
    url: str,
    *,
    method: str = 'GET',
    headers: Mapping[str, str] = {},
    params: Optional[Mapping[str, str]] = None,
    body=None,
    form=None,
    timeout: Optional[float] = 60,
):
    with Client() as client:
        request = client.build_request(
            method,
            url,
            params=params,
            headers=headers,
            data=form,
            json=body,
            timeout=timeout,
        )

        response = client.send(request)
        if response.status_code >= 400:
            raise SparkError.api(response.status_code, SparkApiError.to_cause(request, response))

        return HttpResponse(
            status=response.status_code,
            data=None,
            buffer=response.content,
            headers=response.headers,
            raw_request=request,
            raw_response=response,
        )


@dataclass
class HttpResponse:
    status: int
    data: Union[None, Any, str]
    buffer: bytes
    headers: Headers
    raw_request: Request
    raw_response: Response

    def copy_with(self, **kwargs) -> 'HttpResponse':
        return HttpResponse(
            status=kwargs.get('status', self.status),
            data=kwargs.get('data', self.data),
            buffer=kwargs.get('buffer', self.buffer),
            headers=kwargs.get('headers', self.headers),
            raw_request=kwargs.get('request', self.raw_request),
            raw_response=kwargs.get('response', self.raw_response),
        )


@dataclass(frozen=True)
class UriParams:
    folder: Optional[str] = None
    service: Optional[str] = None
    service_id: Optional[str] = None
    version: Optional[str] = None
    version_id: Optional[str] = None
    proxy: Optional[str] = None
    public: Optional[bool] = False

    @property
    def service_uri(self) -> str:
        """
        Returns the service URI locator's short format if available.
        folder/service[version?]
        """
        return Uri.encode(self, long=False)

    def pick(self, *args: str) -> 'UriParams':
        return UriParams(**{k: v for k, v in self.__dict__.items() if k in args})

    def omit(self, *args: str) -> 'UriParams':
        return UriParams(**{k: v for k, v in self.__dict__.items() if k not in args})

    def encode(self, long: bool = True) -> str:
        return Uri.encode(self, long=long)


class Uri:
    def __init__(self, url: URL):
        self._url = url

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f'<Uri: {self.value}>'

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Uri):
            return False
        return self.value == other.value

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

        if uri.version_id:
            path += f'/version/{uri.version_id}'
        elif uri.service_id:
            path += f'/service/{uri.service_id}'
        elif uri.folder and uri.service:
            path += f'/folders/{uri.folder}/services/{uri.service}'
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
        except SparkError as error:
            raise SparkError.sdk(f'invalid service URI <{resource}>', error) from error
        except Exception as cause:
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
            if folder == 'proxy':
                return UriParams(proxy=service)
            version = None if StringUtils.is_empty(version) else version
            return UriParams(folder=folder, service=service, version=version)
        return UriParams()

    @staticmethod
    def encode(uri: UriParams, long: bool = True) -> str:
        folder, service, version = uri.folder, uri.service, uri.version
        if uri.proxy:
            return f'proxy/{uri.proxy}'
        if uri.version_id:
            return f'version/{uri.version_id}'
        if uri.service_id:
            return f'service/{uri.service_id}'
        if folder and service:
            version = f'[{version}]' if version else ''
            if long:
                return f'folders/{folder}/services/{service}{version}'
            return f'{folder}/{service}{version}'
        return ''

    @staticmethod
    def validate(uri: Union[str, UriParams], message: Optional[str] = None) -> UriParams:
        uri_params = Uri.to_params(uri)
        if StringUtils.is_empty(uri_params.service_uri):
            folder, service = uri_params.folder, uri_params.service
            if folder and not service:
                msg = message or 'service name is missing'
            elif not folder and service:
                msg = message or 'folder name is missing'
            else:
                msg = message or 'service uri locator is required'
            msg += ' :: a uri needs to be of these formats: \n\t- "folder/service[?version]" \n\t-'
            msg += ' "service/service_id" \n\t- "version/version_id" \n\t- "proxy/custom-endpoint"\n'
            raise SparkError.sdk(msg, uri)
        return uri_params
