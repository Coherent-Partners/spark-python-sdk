from __future__ import annotations

from typing import Any, Mapping, Optional, Union

import cspark.sdk.resources as API

from ._auth import Authorization
from ._config import BaseUrl, Config
from ._logger import LoggerOptions
from .resources._base import download as download_file

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
        logger: Union[bool, Mapping[str, Any], LoggerOptions] = True,
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

    @property
    def logs(self) -> API.History:
        return API.History(self.config)

    @property
    def files(self) -> API.Files:
        return API.Files(self.config)

    @property
    def wasm(self) -> API.Wasm:
        return API.Wasm(self.config)

    @staticmethod
    def download(url: str, auth: Optional[Authorization] = None) -> bytes:
        return download_file(url, headers=auth.as_header if auth else {}).buffer


class AsyncClient:
    pass
