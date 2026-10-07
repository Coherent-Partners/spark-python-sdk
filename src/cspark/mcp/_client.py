from __future__ import annotations

import asyncio
import inspect
import json
from contextlib import AsyncExitStack
from types import TracebackType
from typing import Any, Dict, List, Mapping, Optional, Union

from cspark.sdk import BaseUrl, LoggerOptions, SparkError, get_logger
from cspark.sdk._utils import import_optional_module
from httpx import AsyncClient as AsyncHttpClient
from httpx import Timeout

from ._config import McpConfig, McpUrl
from ._errors import SparkMcpError
from ._tools import McpToolsMixin

__all__ = ['AsyncMcpClient', 'McpClient']


def _require_mcp():
    """Import the optional mcp package or raise a clear install hint."""
    try:
        mcp = import_optional_module('mcp', 'cspark[mcp]')
        streamable_http = import_optional_module('mcp.client.streamable_http', 'cspark[mcp]')
        return mcp, streamable_http
    except ImportError as err:
        raise SparkError.sdk(
            'install cspark[mcp] to use the Coherent MCP client (requires Python 3.10+)',
            cause=str(err),
        ) from err


def _normalize_tool_result(result: Any) -> Any:
    """Convert an MCP CallToolResult into a plain Python value."""
    if getattr(result, 'isError', False):
        detail = _content_as_text(result)
        raise SparkMcpError(f'MCP tool call failed: {detail}', cause=result)

    structured = getattr(result, 'structuredContent', None)
    if structured is not None:
        return structured

    text = _content_as_text(result)
    if text is None:
        return result

    try:
        return json.loads(text)
    except (TypeError, json.JSONDecodeError):
        return text


def _content_as_text(result: Any) -> Optional[str]:
    content = getattr(result, 'content', None) or []
    texts: List[str] = []
    for block in content:
        text = getattr(block, 'text', None)
        if text is not None:
            texts.append(text)
        elif isinstance(block, Mapping) and 'text' in block:
            texts.append(str(block['text']))
    if not texts:
        return None
    return texts[0] if len(texts) == 1 else '\n'.join(texts)


class AsyncMcpClient(McpToolsMixin):
    """
    Asynchronous client for Coherent's remote MCP server.

    This is an experimental bridge for agent runtimes and scripts that need the
    same tool surface IDEs see. Prefer ``cspark.sdk`` for normal REST usage.

    Auth: bearer ``token=`` or OAuth2 ``oauth=`` (access token is retrieved on enter).
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
        logger: Union[bool, Mapping[str, Any], LoggerOptions] = True,
    ) -> None:
        _require_mcp()
        self._config = McpConfig(
            base_url=base_url,
            tenant=tenant,
            env=env,
            token=token,
            oauth=oauth,
            timeout=timeout,
            logger=logger,
        )
        self._logger = get_logger(**self._config.logger.__dict__)
        self._stack: Optional[AsyncExitStack] = None
        self._session: Any = None

    @property
    def config(self) -> McpConfig:
        return self._config

    @property
    def session(self) -> Any:
        if self._session is None:
            raise SparkMcpError('MCP session is not connected; use as an async context manager')
        return self._session

    async def _ensure_bearer_token(self) -> None:
        oauth = self._config.auth.oauth
        if oauth and not oauth.access_token:
            async with AsyncHttpClient(timeout=self._config.timeout_in_sec) as http:
                await oauth.aretrieve_token(self._config, http)

    async def __aenter__(self) -> 'AsyncMcpClient':
        mcp, streamable_http = _require_mcp()
        ClientSession = mcp.ClientSession
        create_mcp_http_client = streamable_http.create_mcp_http_client
        streamable_http_client = streamable_http.streamable_http_client

        try:
            await self._ensure_bearer_token()
        except Exception as cause:
            raise SparkMcpError('failed to retrieve OAuth access token for MCP', cause=cause) from cause

        timeout = Timeout(self._config.timeout_in_sec, read=max(300.0, self._config.timeout_in_sec))
        http = create_mcp_http_client(headers=dict(self._config.auth.as_header), timeout=timeout)

        mcp_endpoint = McpUrl(self._config.base_url.to('mcp'), self._config.base_url.tenant).full
        self._stack = AsyncExitStack()
        await self._stack.__aenter__()
        try:
            await self._stack.enter_async_context(http)
            read, write, _get_session_id = await self._stack.enter_async_context(
                streamable_http_client(mcp_endpoint, http_client=http)
            )
            self._session = await self._stack.enter_async_context(ClientSession(read, write))
            self._logger.info(f'connecting to MCP server at {mcp_endpoint}')
            await self._session.initialize()
            self._logger.info('MCP session initialized')
        except Exception as cause:
            await self._stack.__aexit__(type(cause), cause, cause.__traceback__)
            self._stack = None
            self._session = None
            raise SparkMcpError('failed to initialize MCP session', cause=cause) from cause
        return self

    async def __aexit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        if self._stack is not None:
            await self._stack.__aexit__(exc_type, exc, exc_tb)
        self._stack = None
        self._session = None

    async def list_tools(self) -> List[Dict[str, Any]]:
        result = await self.session.list_tools()
        tools = []
        for tool in result.tools:
            tools.append(
                {
                    'name': tool.name,
                    'description': tool.description,
                    'input_schema': tool.inputSchema,
                }
            )
        return tools

    async def call_tool(self, name: str, arguments: Optional[Dict[str, Any]] = None) -> Any:
        self._logger.debug(f'calling MCP tool {name}')
        try:
            result = await self.session.call_tool(name, arguments or {})
        except SparkMcpError:
            raise
        except Exception as cause:
            raise SparkMcpError(f'failed to call MCP tool {name}', cause=cause) from cause
        return _normalize_tool_result(result)


class McpClient:
    """
    Synchronous wrapper around :class:`AsyncMcpClient`.

    Must be used as a context manager so the MCP session stays open across calls.
    Auth: bearer ``token=`` or OAuth2 ``oauth=`` (access token is retrieved on enter).
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
        logger: Union[bool, Mapping[str, Any], LoggerOptions] = True,
    ) -> None:
        self._async = AsyncMcpClient(
            base_url=base_url,
            tenant=tenant,
            env=env,
            token=token,
            oauth=oauth,
            timeout=timeout,
            logger=logger,
        )
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    @property
    def config(self) -> McpConfig:
        return self._async.config

    def __enter__(self) -> 'McpClient':
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._async.__aenter__())
        return self

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        try:
            if self._loop is not None:
                self._loop.run_until_complete(self._async.__aexit__(exc_type, exc, exc_tb))
        finally:
            if self._loop is not None:
                self._loop.close()
            self._loop = None

    def _run(self, coro: Any) -> Any:
        if self._loop is None:
            if inspect.iscoroutine(coro):
                coro.close()
            raise SparkMcpError('McpClient must be used as a context manager')
        return self._loop.run_until_complete(coro)

    def list_tools(self) -> List[Dict[str, Any]]:
        return self._run(self._async.list_tools())

    def call_tool(self, name: str, arguments: Optional[Dict[str, Any]] = None) -> Any:
        return self._run(self._async.call_tool(name, arguments))

    def __getattr__(self, name: str) -> Any:
        attr = getattr(self._async, name)
        if callable(attr):

            def wrapper(*args: Any, **kwargs: Any) -> Any:
                result = attr(*args, **kwargs)
                if inspect.iscoroutine(result):
                    return self._run(result)
                return result

            return wrapper
        return attr
