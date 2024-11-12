from typing import Any, Mapping, Optional, Union

import cspark.wasm.resources as API
from cspark.sdk import BaseUrl, LoggerOptions

from ._config import Config, RunnerUrl

__all__ = ['Client']


class Client:
    def __init__(
        self,
        *,
        base_url: Union[None, str, BaseUrl] = None,
        tenant: Optional[str] = None,
        api_key: Optional[str] = None,
        token: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        retry_interval: Optional[float] = None,
        logger: Union[bool, Mapping[str, Any], LoggerOptions] = True,
    ) -> None:
        self.config = Config(
            base_url=base_url if isinstance(base_url, BaseUrl) else RunnerUrl.of(url=base_url, tenant=tenant),
            api_key=api_key,
            token=token,
            timeout=timeout,
            max_retries=max_retries,
            retry_interval=retry_interval,
            logger=logger,
        )

    @property
    def version(self) -> API.Version:
        return API.Version(self.config)

    @property
    def health(self) -> API.Health:
        return API.Health(self.config)

    @property
    def services(self) -> API.Services:
        return API.Services(self.config)

    @staticmethod
    def health_check(base_url: Optional[str] = None, token: str = 'open', **options):
        config = Config(base_url=RunnerUrl.no_tenant(base_url or ''), token=token, **options)
        with API.Health(config) as health:
            return health.check()

    @staticmethod
    def get_version(base_url: Optional[str] = None, token: str = 'open', **options):
        config = Config(base_url=RunnerUrl.no_tenant(base_url or ''), token=token, **options)
        with API.Version(config) as version:
            return version.get()
