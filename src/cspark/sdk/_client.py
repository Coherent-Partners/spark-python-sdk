from typing import Mapping, Optional

import cspark.sdk.resources as API

from ._config import BaseUrl, Config

__all__ = ['Client']


class Client:
    def __init__(
        self,
        *,
        base_url: Optional[str | BaseUrl] = None,
        oauth: Optional[Mapping[str, str] | str] = None,
        api_key: Optional[str] = None,
        token: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        retry_interval: Optional[float] = None,
        tenant: Optional[str] = None,
        env: Optional[str] = None,
        logger: Optional[bool] = True,
    ) -> None:
        self.config = Config(
            base_url=base_url,
            oauth=oauth,
            api_key=api_key,
            token=token,
            timeout=timeout,
            max_retries=max_retries,
            retry_interval=retry_interval,
            tenant=tenant,
            env=env,
            logger=logger,
        )

    @property
    def services(self) -> API.Services:
        return API.Services(self.config)

    @property
    def batches(self) -> API.Batches:
        return API.Batches(self.config)


class AsyncClient:
    pass
