from json import dumps
from os import getenv
from typing import Optional
from urllib.parse import urlparse

from cspark.sdk import BaseUrl, SparkError
from cspark.sdk import Config as BaseConfig
from httpx import Client as HttpClient

from ._constants import *

__all__ = ['Config', 'RunnerUrl']


class Config(BaseConfig):
    def copy_with(
        self,
        *,
        base_url: Optional[str] = None,
        tenant: Optional[str] = None,
        api_key: Optional[str] = None,
        token: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        retry_interval: Optional[float] = None,
        http_client: Optional[HttpClient] = None,
        **kwargs,  # noqa: ARG002
    ) -> 'Config':
        """Overrides parent's copyWith as `env` and `oauth` are not applicable."""
        url = (
            base_url.copy_with(tenant=tenant)
            if isinstance(base_url, BaseUrl)
            else self.base_url.copy_with(url=base_url, tenant=tenant)
        )
        return Config(
            base_url=url,
            api_key=api_key or self._auth.api_key,
            token=token or self._auth.token,
            timeout=timeout or self._timeout,
            max_retries=max_retries or self._max_retries,
            retry_interval=retry_interval or self._retry_interval,
            http_client=http_client or self.http_client,
        )


class RunnerUrl(BaseUrl):
    def __init__(self, url: Optional[str] = None, tenant: str = ''):
        super().__init__(url or getenv(ENV_VARS.RUNNER_URL) or DEFAULT_RUNNER_URL, tenant)

    def copy_with(self, *, url: Optional[str] = None, tenant: Optional[str] = None, **kwargs) -> 'RunnerUrl':  # noqa: ARG002
        """Overrides parent's copyWith as `env` is not applicable to RunnerUrl."""
        return RunnerUrl.of(url=url or self.value, tenant=tenant or self.tenant)

    @staticmethod
    def of(*, url: Optional[str] = None, tenant: Optional[str] = None, **kwargs) -> 'RunnerUrl':  # noqa: ARG004
        error_msg = 'cannot build base URL from invalid parameters'
        if url:
            parsed_url = urlparse(url.rstrip('/'))  # type: ignore
            paths = str(parsed_url.path).split('/')
            maybe_tenant = paths[1] if len(paths) > 1 else tenant

            if maybe_tenant:
                return RunnerUrl(url=f'{parsed_url.scheme}://{parsed_url.netloc}', tenant=str(maybe_tenant))
            else:
                error_msg = 'tenant name is required'
        elif tenant:
            return RunnerUrl(url='', tenant=str(tenant).strip().lower())

        raise SparkError.sdk(message=error_msg, cause=dumps({'url': url, 'tenant': tenant}))

    @staticmethod
    def no_tenant(url: str = getenv(ENV_VARS.RUNNER_URL) or DEFAULT_RUNNER_URL) -> 'RunnerUrl':
        """Builds a base URL from the given URL without a tenant (only valid for Version/Health API Resources)"""
        return RunnerUrl(url, tenant='')
