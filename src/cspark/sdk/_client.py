from __future__ import annotations

from types import TracebackType
from typing import Any, Mapping, Optional, Union

import cspark.sdk.resources as API
from httpx import AsyncClient as AsyncHttpClient
from httpx import Client as HttpClient

from ._auth import Authorization
from ._config import BaseUrl, Config, HealthUrl
from ._errors import SparkApiError, SparkError
from ._logger import LoggerOptions

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
        base_url: Union[str, BaseUrl], token: str = 'open', http_client: Optional[HttpClient] = None, **options: Any
    ):
        """Checks the health status of the Coherent Spark environment."""
        config = Config(base_url=HealthUrl.when(base_url), token=token, **options)
        with http_client or HttpClient(timeout=config.timeout_in_sec) as client:
            return API.Health(config, client).check()

    @staticmethod
    def download(url: str, auth: Optional[Authorization] = None) -> bytes:
        """Downloads a file from the given URL."""
        try:
            with HttpClient() as client:
                request = client.build_request('GET', url, headers=auth.as_header if auth else {})
                response = client.send(request)
                if response.status_code >= 400:
                    raise SparkError.api(response.status_code, SparkApiError.to_cause(request, response))
            return response.content
        except Exception as exc:
            raise SparkError.sdk(f'failed to download file from {url}', cause=exc) from exc


class AsyncClient:
    """
    The main entry point for the Coherent Spark SDK "async" client.

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

    @property
    def health(self) -> API.AsyncHealth:
        """The resource to manage health checks."""
        return API.AsyncHealth(self.config, self.http_client)

    @property
    def folders(self) -> API.AsyncFolders:
        """The resource to manage Folders API."""
        return API.AsyncFolders(self.config, self.http_client)

    @property
    def services(self) -> API.AsyncServices:
        """The resource to manage Services API."""
        return API.AsyncServices(self.config, self.http_client)

    @property
    def transforms(self) -> API.AsyncTransforms:
        """The resource to manage Transforms API."""
        return API.AsyncTransforms(self.config, self.http_client)

    @property
    def batches(self) -> API.AsyncBatches:
        """The resource to manage asynchronous batch processing."""
        return API.AsyncBatches(self.config, self.http_client)

    @property
    def logs(self) -> API.AsyncHistory:
        """The resource to manage service execution logs."""
        return API.AsyncHistory(self.config, self.http_client)

    @property
    def files(self) -> API.AsyncFiles:
        """The resource to manage files."""
        return API.AsyncFiles(self.config, self.http_client)

    @property
    def wasm(self) -> API.AsyncWasm:
        """The resource to manage a service's WebAssembly module."""
        return API.AsyncWasm(self.config, self.http_client)

    @property
    def impex(self) -> API.AsyncImpEx:
        """The resource to import and export Spark services."""
        return API.AsyncImpEx.only(self.config, self.http_client)

    @staticmethod
    async def health_check(
        base_url: Union[str, BaseUrl],
        token: str = 'open',
        http_client: Optional[AsyncHttpClient] = None,
        **options: Any,
    ):
        """Checks the health status of the Coherent Spark environment."""
        config = Config(base_url=HealthUrl.when(base_url), token=token, **options)
        async with http_client or AsyncHttpClient(timeout=config.timeout_in_sec) as client:
            return await API.AsyncHealth(config, client).check()

    @staticmethod
    async def download(url: str, auth: Optional[Authorization] = None) -> bytes:
        """Downloads a file from the given URL."""
        try:
            async with AsyncHttpClient() as client:
                request = client.build_request('GET', url, headers=auth.as_header if auth else {})
                response = await client.send(request)
                if response.status_code >= 400:
                    raise SparkError.api(response.status_code, SparkApiError.to_cause(request, response))
            return await response.aread()
        except Exception as exc:
            raise SparkError.sdk(f'failed to download file from {url}', cause=exc) from exc
