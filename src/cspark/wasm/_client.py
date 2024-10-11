from typing import Any, Mapping, Optional, Union

import cspark.wasm.resources as API
from cspark.sdk import BaseUrl, Config, LoggerOptions

from ._constants import DEFAULT_RUNNER_URL

__all__ = ['Client']


class Client:
    def __init__(
        self,
        tenant: str,
        *,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        token: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        retry_interval: Optional[float] = None,
        logger: Union[bool, Mapping[str, Any], LoggerOptions] = True,
    ) -> None:
        self.config = Config(
            base_url=BaseUrl(base_url or DEFAULT_RUNNER_URL, tenant=tenant),
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
    def health_check(base_url: str = DEFAULT_RUNNER_URL):
        config = Config(base_url=BaseUrl(base_url, tenant=''), token='open')
        with API.Health(config) as health:
            return health.check()

    @staticmethod
    def get_version(base_url: str = DEFAULT_RUNNER_URL):
        config = Config(base_url=BaseUrl(base_url, tenant=''), token='open')
        with API.Version(config) as version:
            return version.get()
