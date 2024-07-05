from __future__ import annotations

import json
import os
from typing import Mapping, Optional, cast
from urllib.parse import urlparse

from ._constants import *
from ._errors import SparkError
from ._utils import is_str_empty
from ._validators import Validators

__all__ = ['Config', 'BaseUrl']


class Config:
    _options: str
    extra_headers: Mapping[str, str] = {}

    def __init__(
        self,
        *,
        base_url: Optional[str | BaseUrl] = None,
        api_key: Optional[str] = None,
        token: Optional[str] = None,
        oauth: Optional[Mapping[str, str] | str] = None,
        timeout: Optional[float] = DEFAULT_TIMEOUT_IN_MS,
        max_retries: Optional[int] = DEFAULT_MAX_RETRIES,
        retry_interval: Optional[float] = DEFAULT_RETRY_INTERVAL,
        tenant: Optional[str] = None,
        env: Optional[str] = None,
        logger: Optional[bool] = True,
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
        self._logger = logger

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

    @property
    def has_headers(self) -> bool:
        return len(self.extra_headers) > 0

    @property
    def base_url(self) -> BaseUrl:
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
    def logger(self) -> bool:
        return cast(bool, self._logger or False)

    def copy_with(
        self,
        *,
        tenant: Optional[str] = None,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        token: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        retry_interval: Optional[float] = None,
        env: Optional[str] = None,
    ) -> Config:
        base_url = base_url or self._base_url.value
        tenant = tenant or self._base_url.tenant
        env = env or self._base_url.tenant
        url = base_url if isinstance(base_url, BaseUrl) else BaseUrl.of(url=base_url, tenant=tenant, env=env)
        return Config(
            base_url=url,
            api_key=api_key or self._auth.api_key,
            token=token or self._auth.token,
            timeout=timeout or self._timeout,
            max_retries=max_retries or self._max_retries,
            retry_interval=retry_interval or self._retry_interval,
        )

    def __str__(self) -> str:
        return self._options


class BaseUrl:
    def __init__(self, url: str, tenant: str):
        self._base: str = url
        self._tenant: str = tenant

    @property
    def tenant(self) -> str:
        return self._tenant

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

    @staticmethod
    def of(*, url: Optional[str] = None, tenant: Optional[str] = None, env: Optional[str] = None) -> BaseUrl:
        str_validator = Validators.empty_str()
        url_validator = Validators.base_url()

        if url_validator.is_valid(url):
            parsed_url = urlparse(url)
            paths = str(parsed_url.path).split('/')
            maybe_tenant = paths[1] if len(paths) > 1 else tenant

            if str_validator.is_valid(maybe_tenant, 'tenant name is required'):
                base_url = f'{parsed_url.scheme}://{parsed_url.netloc}'
                return BaseUrl(url=base_url, tenant=str(maybe_tenant))
        elif not is_str_empty(tenant) and not is_str_empty(env):
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
