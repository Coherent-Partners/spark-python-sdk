from __future__ import annotations

from types import TracebackType
from typing import Any, Mapping, Optional, Union

import cspark.wasm.resources as API
from cspark.sdk import BaseUrl, LoggerOptions
from httpx import AsyncClient as AsyncHttpClient
from httpx import Client as HttpClient

from ._config import Config, RunnerUrl

__all__ = ['Client', 'AsyncClient']


class Client:
    """
    The main entry point for the Hybrid Runner client.

    Hybrid Runners offer a smaller subset of functionality compared to the SaaS API.
    Thus, extending 'cspark.sdk' to support the Hybrid Runner API is a good way
    to keep the codebase consistent and maintainable.
    """

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
        http_client: Optional[HttpClient] = None,
        logger: Union[bool, Mapping[str, Any], LoggerOptions] = True,
    ) -> None:
        self._config = Config(
            base_url=base_url if isinstance(base_url, BaseUrl) else RunnerUrl.of(url=base_url, tenant=tenant),
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
    def version(self) -> API.Version:
        return API.Version(self.config, self.http_client)

    @property
    def health(self) -> API.Health:
        return API.Health(self.config, self.http_client)

    @property
    def status(self) -> API.Status:
        return API.Status(self.config, self.http_client)

    @property
    def services(self) -> API.Services:
        return API.Services(self.config, self.http_client)

    @staticmethod
    def health_check(
        base_url: Optional[str] = None, token: str = 'open', http_client: Optional[HttpClient] = None, **options: Any
    ):
        config = Config(base_url=RunnerUrl.no_tenant(base_url or ''), token=token, **options)
        with http_client or HttpClient(timeout=config.timeout_in_sec) as client:
            return API.Health(config, client).check()

    @staticmethod
    def get_version(
        base_url: Optional[str] = None, token: str = 'open', http_client: Optional[HttpClient] = None, **options: Any
    ):
        config = Config(base_url=RunnerUrl.no_tenant(base_url or ''), token=token, **options)
        with http_client or HttpClient(timeout=config.timeout_in_sec) as client:
            return API.Version(config, client).get()

    @staticmethod
    def get_status(
        base_url: Optional[str] = None, token: str = 'open', http_client: Optional[HttpClient] = None, **options: Any
    ):
        config = Config(base_url=RunnerUrl.no_tenant(base_url or ''), token=token, **options)
        with http_client or HttpClient(timeout=config.timeout_in_sec) as client:
            return API.Status(config, client).get()


class AsyncClient:
    """
    The main entry point for the Hybrid Runner "async" client.

    This class provides access to all the resources available in the Hybrid Runner API.
    Do note that this client is asynchronous and non-blocking. For a synchronous client,
    use the `Client` class.
    """

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
        http_client: Optional[AsyncHttpClient] = None,
        logger: Union[bool, Mapping[str, Any], LoggerOptions] = True,
    ) -> None:
        self._config = Config(
            base_url=base_url if isinstance(base_url, BaseUrl) else RunnerUrl.of(url=base_url, tenant=tenant),
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
    def version(self) -> API.AsyncVersion:
        return API.AsyncVersion(self._config, self.http_client)

    @property
    def health(self) -> API.AsyncHealth:
        return API.AsyncHealth(self._config, self.http_client)

    @property
    def status(self) -> API.AsyncStatus:
        return API.AsyncStatus(self._config, self.http_client)

    @property
    def services(self) -> API.AsyncServices:
        return API.AsyncServices(self._config, self.http_client)

    @staticmethod
    async def health_check(
        base_url: Optional[str] = None,
        token: str = 'open',
        http_client: Optional[AsyncHttpClient] = None,
        **options: Any,
    ):
        config = Config(base_url=RunnerUrl.no_tenant(base_url or ''), token=token, **options)
        async with http_client or AsyncHttpClient(timeout=config.timeout_in_sec) as client:
            return await API.AsyncHealth(config, client).check()

    @staticmethod
    async def get_version(
        base_url: Optional[str] = None,
        token: str = 'open',
        http_client: Optional[AsyncHttpClient] = None,
        **options: Any,
    ):
        config = Config(base_url=RunnerUrl.no_tenant(base_url or ''), token=token, **options)
        async with http_client or AsyncHttpClient(timeout=config.timeout_in_sec) as client:
            return await API.AsyncVersion(config, client).get()

    @staticmethod
    async def get_status(
        base_url: Optional[str] = None,
        token: str = 'open',
        http_client: Optional[AsyncHttpClient] = None,
        **options: Any,
    ):
        config = Config(base_url=RunnerUrl.no_tenant(base_url or ''), token=token, **options)
        async with http_client or AsyncHttpClient(timeout=config.timeout_in_sec) as client:
            return await API.AsyncStatus(config, client).get()
