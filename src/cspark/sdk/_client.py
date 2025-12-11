from __future__ import annotations

from types import TracebackType
from typing import Any, Mapping, Optional, Union

import cspark.sdk.resources as API
from httpx import AsyncClient as AsyncHttpClient
from httpx import Client as HttpClient

from ._auth import Authorization
from ._config import BaseUrl, Config, HealthUrl
from ._logger import LoggerOptions
from .resources._base import download as download_file

__all__ = ['Client', 'AsyncClient']


class Client:
    """
    The main entry point for the Coherent Spark SDK client.

    This class provides access to all the resources available in the SDK, including
    the `folders`, and `services` APIs, as well as the `impex` and `wasm` utilities.
    Do note that this client is synchronous and blocking. For an asynchronous client,
    use the `AsyncClient` class.

    A custom HTTP client may be used to add extra capabilities (proxy, auth, verify, etc).

    Visit the main documentation page for more details on how to use the SDK.
    See https://github.com/Coherent-Partners/spark-python-sdk/blob/main/docs
    to learn more about the SDK and its capabilities.
    """

    def __init__(
        self,
        *,
        base_url: Union[None, str, BaseUrl] = None,
        tenant: Optional[str] = None,
        env: Optional[str] = None,
        oauth: Union[None, Mapping[str, str], str] = None,
        api_key: Optional[str] = None,
        token: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        retry_interval: Optional[float] = None,
        logger: Union[bool, Mapping[str, Any], LoggerOptions] = True,
        http_client: Optional[HttpClient] = None,
    ) -> None:
        self._config = Config(
            base_url=base_url,
            tenant=tenant,
            env=env,
            oauth=oauth,
            api_key=api_key,
            token=token,
            timeout=timeout,
            max_retries=max_retries,
            retry_interval=retry_interval,
            logger=logger,
        )
        self.http_client = http_client or HttpClient(timeout=self._config.timeout_in_sec)

    def __enter__(self) -> Client:
        return self

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        self.close()

    def close(self):
        if not self.http_client.is_closed:
            self.http_client.close()

    @property
    def config(self) -> Config:
        return self._config

    @property
    def health(self) -> API.Health:
        """The resource to manage health checks."""
        return API.Health(self.config, self.http_client)

    @property
    def folders(self) -> API.Folders:
        """The resource to manage Folders API."""
        return API.Folders(self.config, self.http_client)

    @property
    def services(self) -> API.Services:
        """The resource to manage Services API."""
        return API.Services(self.config, self.http_client)

    @property
    def transforms(self) -> API.Transforms:
        """The resource to manage Transforms API."""
        return API.Transforms(self.config, self.http_client)

    @property
    def batches(self) -> API.Batches:
        """The resource to manage asynchronous batch processing."""
        return API.Batches(self.config, self.http_client)

    @property
    def logs(self) -> API.History:
        """The resource to manage service execution logs."""
        return API.History(self.config, self.http_client)

    @property
    def files(self) -> API.Files:
        """The resource to manage files."""
        return API.Files(self.config, self.http_client)

    @property
    def wasm(self) -> API.Wasm:
        """The resource to manage a service's WebAssembly module."""
        return API.Wasm(self.config, self.http_client)

    @property
    def impex(self) -> API.ImpEx:
        """The resource to import and export Spark services."""
        return API.ImpEx.only(self.config, self.http_client)

    @staticmethod
    def health_check(
        base_url: Union[str, BaseUrl], token: str = 'open', http_client: Optional[HttpClient] = None, **options
    ):
        """Checks the health status of the Coherent Spark environment."""
        config = Config(base_url=HealthUrl.when(base_url), token=token, **options)
        http_client = http_client or HttpClient(timeout=config.timeout_in_sec)
        try:
            return API.Health(config, http_client).check()
        finally:
            if not http_client.is_closed:
                http_client.close()

    @staticmethod
    def download(url: str, auth: Optional[Authorization] = None) -> bytes:
        """Downloads a file from the given URL."""
        return download_file(url, headers=auth.as_header if auth else {}).buffer


class AsyncClient:
    """
    The main entry point for the Coherent Spark SDK asynchronous client.

    This class provides access to all the resources available in the SDK.
    Do note that this client is asynchronous and non-blocking. For a synchronous client,
    use the `Client` class.
    """

    def __init__(
        self,
        *,
        base_url: Union[None, str, BaseUrl] = None,
        tenant: Optional[str] = None,
        env: Optional[str] = None,
        oauth: Union[None, Mapping[str, str], str] = None,
        api_key: Optional[str] = None,
        token: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        retry_interval: Optional[float] = None,
        logger: Union[bool, Mapping[str, Any], LoggerOptions] = True,
        http_client: Optional[AsyncHttpClient] = None,
    ) -> None:
        self._config = Config(
            base_url=base_url,
            tenant=tenant,
            env=env,
            oauth=oauth,
            api_key=api_key,
            token=token,
            timeout=timeout,
            max_retries=max_retries,
            retry_interval=retry_interval,
            logger=logger,
        )
        self.http_client = http_client or AsyncHttpClient(timeout=self._config.timeout_in_sec)

    async def __aenter__(self) -> AsyncClient:
        return self

    async def __aexit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        await self.close()

    async def close(self):
        if not self.http_client.is_closed:
            await self.http_client.aclose()

    @property
    def config(self) -> Config:
        return self._config
