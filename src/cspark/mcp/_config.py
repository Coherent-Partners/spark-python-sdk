from __future__ import annotations

from typing import Any, Mapping, Optional, Union

from cspark.sdk import BaseUrl, LoggerOptions, SparkError
from cspark.sdk import Config as BaseConfig
from cspark.sdk._utils import StringUtils

__all__ = ['McpConfig', 'McpUrl']


class McpUrl(BaseUrl):
    """Coherent remote MCP server URL: https://mcp.{env}.coherent.global/{tenant}/mcp"""

    @property
    def full(self) -> str:
        return f'{self.to("mcp")}/{self.tenant}/mcp'

    @staticmethod
    def of(
        *, url: Union[None, str, BaseUrl] = None, tenant: Optional[str] = None, env: Optional[str] = None
    ) -> 'McpUrl':
        base_url = url if isinstance(url, BaseUrl) else BaseUrl.of(url=url, tenant=tenant, env=env)
        return McpUrl(url=base_url.to('mcp'), tenant=base_url.tenant)


class McpConfig(BaseConfig):
    """
    Configuration for the Coherent MCP client.

    Supports bearer token or OAuth2 client credentials only (no API key).
    When using OAuth2, retrieve an access token before connecting (the MCP
    clients do this automatically on enter).
    """

    def __init__(
        self,
        *,
        base_url: Union[None, str, BaseUrl, McpUrl] = None,
        tenant: Optional[str] = None,
        env: Optional[str] = None,
        token: Optional[str] = None,
        oauth: Union[None, Mapping[str, str], str] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        retry_interval: Optional[float] = None,
        logger: Union[bool, Mapping[str, Any], LoggerOptions] = True,
    ) -> None:
        try:
            super().__init__(
                base_url=base_url,
                tenant=tenant,
                env=env,
                api_key='',  # Pass empty string so CSPARK_API_KEY is not picked up.
                token=token,
                oauth=oauth,
                timeout=timeout,
                max_retries=max_retries,
                retry_interval=retry_interval,
                logger=logger,
            )
            if not isinstance(self.base_url, McpUrl):
                self._base_url = McpUrl.of(url=self.base_url)
        except SparkError as err:
            raise SparkError.sdk(
                message='MCP client requires a bearer token or OAuth2 credentials; '
                'API key authentication is not supported.\n'
                'Provide token=/CSPARK_BEARER_TOKEN or oauth= client credentials.\n'
                'Browser login is only supported by IDE MCP connectors.',
                cause=getattr(err, 'cause', str(err)),
            ) from err

        if self._auth.type == 'api_key':
            raise SparkError.sdk(
                message='MCP client does not support API key authentication; use a bearer token or OAuth2',
                cause=str(self._auth.type),
            )

        # Prefer masked token in the printable options string.
        self._options = str(
            {
                'base_url': self._base_url.full,
                'oauth': str(self._auth.oauth) if self._auth.oauth else None,
                'token': StringUtils.mask(self._auth.token) if self._auth.token else None,
                'timeout': self._timeout,
                'max_retries': self._max_retries,
                'retry_interval': self._retry_interval,
                'logger': self._logger,
            }
        )

    def copy_with(
        self,
        *,
        base_url: Optional[str] = None,
        tenant: Optional[str] = None,
        env: Optional[str] = None,
        token: Optional[str] = None,
        oauth: Union[None, Mapping[str, str], str] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        retry_interval: Optional[float] = None,
        **kwargs: Any,  # noqa: ARG002
    ) -> 'McpConfig':
        """Overrides parent — API key is not applicable; oauth is supported."""
        if isinstance(base_url, BaseUrl):
            url = base_url.copy_with(tenant=tenant, env=env)
        else:
            url = self.base_url.copy_with(url=base_url, tenant=tenant, env=env)

        return McpConfig(
            base_url=url,
            token=token or self._auth.token,
            oauth=oauth or (self._auth.oauth.to_dict() if self._auth.oauth else None),
            timeout=timeout or self._timeout,
            max_retries=max_retries or self._max_retries,
            retry_interval=retry_interval or self._retry_interval,
            logger=self._logger,
        )
