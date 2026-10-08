from __future__ import annotations

import os
import sys
from unittest.mock import AsyncMock, MagicMock

import pytest
from cspark.mcp import AsyncMcpClient, McpClient, SparkMcpError
from cspark.mcp._client import _normalize_tool_result
from cspark.mcp._tools import omit_none

requires_mcp = pytest.mark.skipif(
    sys.version_info < (3, 10),
    reason='cspark[mcp] requires Python 3.10+',
)


def test_omit_none():
    assert omit_none({'a': 1, 'b': None, 'c': False}) == {'a': 1, 'c': False}


def test_normalize_structured_content():
    result = MagicMock(isError=False, structuredContent={'ok': True}, content=[])
    assert _normalize_tool_result(result) == {'ok': True}


def test_normalize_json_text():
    block = MagicMock(text='{"value": 42}')
    result = MagicMock(isError=False, structuredContent=None, content=[block])
    assert _normalize_tool_result(result) == {'value': 42}


def test_normalize_error_raises():
    block = MagicMock(text='boom')
    result = MagicMock(isError=True, structuredContent=None, content=[block])
    with pytest.raises(SparkMcpError, match='boom'):
        _normalize_tool_result(result)


@pytest.mark.anyio
async def test_execute_v3_maps_request_payload():
    client = AsyncMcpClient.__new__(AsyncMcpClient)
    client.call_tool = AsyncMock(return_value={'ok': True})

    await AsyncMcpClient.execute_v3(
        client,
        folder='f',
        service='s',
        request_payload={'inputs': {'x': 1}},
        version='1.0.0',
    )

    client.call_tool.assert_awaited_once_with(
        'spark_execute_v3',
        {
            'folder': 'f',
            'service': 's',
            'version': '1.0.0',
            'requestPayload': {'inputs': {'x': 1}},
        },
    )


@pytest.mark.anyio
async def test_service_info_omits_unset_fields():
    client = AsyncMcpClient.__new__(AsyncMcpClient)
    client.call_tool = AsyncMock(return_value={'ok': True})

    await AsyncMcpClient.service_info(client, folder='f', service='s')

    client.call_tool.assert_awaited_once_with(
        'spark_service_info',
        {'folder': 'f', 'service': 's'},
    )


@pytest.mark.anyio
async def test_run_testbed_tool_name():
    client = AsyncMcpClient.__new__(AsyncMcpClient)
    client.call_tool = AsyncMock(return_value={'run_id': 'r1'})

    await AsyncMcpClient.run_testbed(client, folder='f', service='s', testbed='tb')

    client.call_tool.assert_awaited_once_with(
        'spark_run_testbed',
        {'folder': 'f', 'service': 's', 'testbed': 'tb'},
    )


@requires_mcp
def test_sync_client_requires_context_manager():
    client = McpClient(env='test', tenant='t', token='tok')
    with pytest.raises(SparkMcpError, match='context manager'):
        client.list_tools()


@requires_mcp
def test_async_session_requires_context_manager():
    client = AsyncMcpClient(env='test', tenant='t', token='tok')
    with pytest.raises(SparkMcpError, match='not connected'):
        _ = client.session


@requires_mcp
@pytest.mark.skipif(
    os.getenv('CSPARK_MCP_INTEGRATION') != '1',
    reason='set CSPARK_MCP_INTEGRATION=1 with CSPARK_BEARER_TOKEN, env, and tenant to run',
)
@pytest.mark.anyio
async def test_live_list_tools():
    async with AsyncMcpClient(
        env=os.environ['CSPARK_ENV'],
        tenant=os.environ['CSPARK_TENANT'],
        token=os.environ['CSPARK_BEARER_TOKEN'],
    ) as mcp:
        tools = await mcp.list_tools()
        assert isinstance(tools, list)
        assert any(t['name'].startswith('spark_') for t in tools)
