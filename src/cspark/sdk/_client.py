from __future__ import annotations

from typing import Any, Mapping, Optional, Union

import cspark.sdk.resources as API

from ._auth import Authorization
from ._config import BaseUrl, Config
from ._logger import LoggerOptions
from .resources._base import download as download_file

__all__ = ['Client']


class Client:
    """
    The main entry point for the Coherent Spark SDK client.

    This class provides access to all the resources available in the SDK, including
    the `folders`, and `services` APIs, as well as the `impex` and `wasm` utilities.
    Do note that this client is synchronous and blocking. For an asynchronous client,
    use the `AsyncClient` class.

    Visit the main documentation page for more details on how to use the SDK.
    See https://github.com/Coherent-Partners/spark-python-sdk/blob/main/docs
    to learn more about the SDK and its capabilities.
    """

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
        """The resource to manage Services API."""
        return API.Services(self.config)

    @property
    def batches(self) -> API.Batches:
        """The resource to manage asynchronous batch processing."""
        return API.Batches(self.config)

    @property
    def logs(self) -> API.History:
        """The resource to manage service execution logs."""
        return API.History(self.config)

    @property
    def files(self) -> API.Files:
        """The resource to manage files."""
        return API.Files(self.config)

    @property
    def wasm(self) -> API.Wasm:
        """The resource to manage a service's WebAssembly module."""
        return API.Wasm(self.config)

    @property
    def impex(self) -> API.ImpEx:
        """The resource to import and export Spark services."""
        return API.ImpEx.only(self.config)

    @staticmethod
    def download(url: str, auth: Optional[Authorization] = None) -> bytes:
        """Downloads a file from the given URL."""
        return download_file(url, headers=auth.as_header if auth else {}).buffer


class AsyncClient:
    pass
