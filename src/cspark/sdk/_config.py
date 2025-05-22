import json
import os
import re
from typing import Any, Mapping, Optional, Union, cast
from urllib.parse import urlparse

from httpx import Client as HttpClient

from ._constants import *
from ._errors import SparkError
from ._logger import LoggerOptions
from ._utils import StringUtils
from ._validators import Validators

__all__ = ['Config', 'BaseUrl', 'HealthUrl']


class Config:
    _options: str
    _logger: LoggerOptions

    def __init__(
        self,
        *,
        base_url: Union[None, str, 'BaseUrl'] = None,
        tenant: Optional[str] = None,
        env: Optional[str] = None,
        api_key: Optional[str] = None,
        token: Optional[str] = None,
        oauth: Union[None, Mapping[str, str], str] = None,
        timeout: Optional[float] = DEFAULT_TIMEOUT_IN_MS,
        max_retries: Optional[int] = DEFAULT_MAX_RETRIES,
        retry_interval: Optional[float] = DEFAULT_RETRY_INTERVAL,
        logger: Union[bool, Mapping[str, Any], LoggerOptions] = True,
        # A custom HTTP client to use with extra capabilities (proxy, auth, verify, etc).
        http_client: Optional[HttpClient] = None,
    ) -> None:
        from ._auth import Authorization  # NOTE: help avoid circular import

        num_validator = Validators.positive_num()

        base_url = os.getenv(ENV_VARS.BASE_URL) if base_url is None else base_url
        api_key = os.getenv(ENV_VARS.API_KEY) if api_key is None else api_key
        token = os.getenv(ENV_VARS.BEARER_TOKEN) if token is None else token

        self._base_url = base_url if isinstance(base_url, BaseUrl) else BaseUrl.of(url=base_url, tenant=tenant, env=env)
        self._auth = Authorization(api_key=api_key, token=token, oauth=oauth)
        self._timeout = timeout if num_validator.is_valid(timeout) else DEFAULT_TIMEOUT_IN_MS
        self._max_retries = max_retries if num_validator.is_valid(max_retries) else DEFAULT_MAX_RETRIES
        self._retry_interval = retry_interval if num_validator.is_valid(retry_interval) else DEFAULT_RETRY_INTERVAL
        self._logger = LoggerOptions.when(logger)

        self.http_client = http_client
        self.extra_headers = {}
        self._options = str(
            {
                'base_url': self._base_url.full,
                'oauth': str(self._auth.oauth) if self._auth.oauth else None,
                'api_key': self._auth.api_key,
                'token': self._auth.token,
                'timeout': self._timeout,
                'max_retries': self._max_retries,
                'retry_interval': self._retry_interval,
                'logger': self._logger,
            }
        )

    def __str__(self) -> str:
        return self._options

    @property
    def has_headers(self) -> bool:
        return len(self.extra_headers) > 0

    @property
    def base_url(self) -> 'BaseUrl':
        return self._base_url

    @property
    def auth(self):
        return self._auth

    @property
    def timeout(self) -> float:
        return cast(float, self._timeout)

    @property
    def max_retries(self) -> int:
        return cast(int, self._max_retries)

    @property
    def retry_interval(self) -> float:
        return cast(float, self._retry_interval)

    @property
    def logger(self) -> LoggerOptions:
        return self._logger

    def copy_with(
        self,
        *,
        base_url: Optional[str] = None,
        tenant: Optional[str] = None,
        env: Optional[str] = None,
        oauth: Union[None, Mapping[str, str], str] = None,
        api_key: Optional[str] = None,
        token: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        retry_interval: Optional[float] = None,
        http_client: Optional[HttpClient] = None,
    ) -> 'Config':
        url = (
            base_url.copy_with(tenant=tenant, env=env)
            if isinstance(base_url, BaseUrl)
            else self.base_url.copy_with(url=base_url, tenant=tenant, env=env)
        )
        return Config(
            base_url=url,
            oauth=oauth or self._auth.oauth.to_dict() if self._auth.oauth else None,
            api_key=api_key or self._auth.api_key,
            token=token or self._auth.token,
            timeout=timeout or self._timeout,
            max_retries=max_retries or self._max_retries,
            retry_interval=retry_interval or self._retry_interval,
            http_client=http_client or self.http_client,
        )


class BaseUrl:
    __services = ['excel', 'keycloak', 'utility', 'entitystore']
    _service: Optional[str]
    _env: Optional[str]

    def __init__(self, url: str, tenant: str):
        match = re.match(r'https://([^\.]+)\.((?:[^\.]+\.)?[^\.]+)\.coherent\.global', url)
        if match:
            service, env = match.groups()
            self._env = str(env).strip().lower() if env else None
            self._service = str(service).strip().lower() in self.__services and service or 'excel'
            self._base = f'https://{self._service}.{self._env}.coherent.global'
        else:
            self._env = None
            self._service = None
            self._base = url
        self._tenant = tenant

    @property
    def tenant(self) -> str:
        return self._tenant

    @property
    def env(self) -> Optional[str]:
        return self._env

    @property
    def service(self) -> Optional[str]:
        return self._service

    @property
    def full(self) -> str:
        return f'{self._base}/{self._tenant}'

    @property
    def value(self) -> str:
        return self._base

    @property
    def oauth2(self) -> str:
        return f'{self.to("keycloak")}/auth/realms/{self._tenant}'

    def to(self, service: str = 'excel', with_tenant: bool = False) -> str:
        return (self.full if with_tenant else self.value).replace('excel', service)

    def copy_with(
        self, *, url: Optional[str] = None, tenant: Optional[str] = None, env: Optional[str] = None
    ) -> 'BaseUrl':
        tenant, env = tenant or self._tenant, env or self._env
        return BaseUrl.of(url=url, tenant=tenant) if url else BaseUrl.of(tenant=tenant, env=env)

    @staticmethod
    def of(*, url: Optional[str] = None, tenant: Optional[str] = None, env: Optional[str] = None) -> 'BaseUrl':
        str_validator = Validators.empty_str()
        url_validator = Validators.base_url()

        if url_validator.is_valid(url):
            parsed_url = urlparse(url.rstrip('/'))  # pyright: ignore[reportOptionalMemberAccess]
            paths = str(parsed_url.path).split('/')
            maybe_tenant = paths[1] if len(paths) > 1 else tenant

            if str_validator.is_valid(maybe_tenant, 'tenant name is required'):
                base_url = f'{parsed_url.scheme}://{parsed_url.netloc}'
                return BaseUrl(url=base_url, tenant=str(maybe_tenant))
        elif StringUtils.is_not_empty(tenant) and StringUtils.is_not_empty(env):
            base_url = f'https://excel.{str(env).strip().lower()}.coherent.global'
            return BaseUrl(url=base_url, tenant=str(tenant).strip().lower())
        else:
            # capture errors for missing parameters
            str_validator.is_valid(env, 'environment name is missing') and str_validator.is_valid(
                tenant, 'tenant name is missing'
            )  # pyright: ignore[reportUnusedExpression]

        errors = url_validator.errors  # + str_validator.errors
        raise SparkError.sdk(
            message='; '.join(e.message for e in errors)
            if len(errors) > 0
            else 'cannot build base URL from invalid parameters',
            cause=json.dumps({'url': url, 'tenant': tenant, 'env': env}),
        )


class HealthUrl(BaseUrl):
    def __init__(self, base_url: str):
        super().__init__(base_url, tenant='')

    @staticmethod
    def when(url: Union[str, BaseUrl]) -> 'HealthUrl':
        parsed_url = urlparse(url if isinstance(url, str) else url.to('excel'))
        if parsed_url.scheme:
            return HealthUrl(f'{parsed_url.scheme}://{parsed_url.netloc}')
        else:
            return HealthUrl(f'https://excel.{url}.coherent.global')  # otherwise treat as environment
