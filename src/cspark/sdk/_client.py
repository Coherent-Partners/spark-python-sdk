from typing import Any, Mapping, Optional, Union

import cspark.sdk.resources as API
from httpx import Client as HttpClient

from ._auth import Authorization
from ._config import BaseUrl, Config, HealthUrl
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
        base_url: Union[None, str, BaseUrl] = None,
        tenant: Optional[str] = None,
        env: Optional[str] = None,
        oauth: Union[None, Mapping[str, str], str] = None,
        api_key: Optional[str] = None,
        token: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        retry_interval: Optional[float] = None,
        http_client: Optional[HttpClient] = None,
        logger: Union[bool, Mapping[str, Any], LoggerOptions] = True,
    ) -> None:
        self.config = Config(
            base_url=base_url,
            tenant=tenant,
            env=env,
            oauth=oauth,
            api_key=api_key,
            token=token,
            timeout=timeout,
            max_retries=max_retries,
            retry_interval=retry_interval,
            http_client=http_client,
            logger=logger,
        )

    @property
    def health(self) -> API.Health:
        """The resource to manage health checks."""
        return API.Health(self.config)

    @property
    def folders(self) -> API.Folders:
        """The resource to manage Folders API."""
        return API.Folders(self.config)

    @property
    def services(self) -> API.Services:
        """The resource to manage Services API."""
        return API.Services(self.config)

    @property
    def transforms(self) -> API.Transforms:
        """The resource to manage Transforms API."""
        return API.Transforms(self.config)

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
    def health_check(base_url: Union[str, BaseUrl], token: str = 'open', **options):
        """Checks the health status of the Coherent Spark environment."""
        config = Config(base_url=HealthUrl.when(base_url), token=token, **options)
        with API.Health(config) as health:
            return health.check()

    @staticmethod
    def download(url: str, auth: Optional[Authorization] = None) -> bytes:
        """Downloads a file from the given URL."""
        return download_file(url, headers=auth.as_header if auth else {}).buffer


class AsyncClient:
    pass
