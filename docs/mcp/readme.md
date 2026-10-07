# MCP Client (experimental)

> **Experimental:** Coherent MCP is tenant-gated and evolving. Tool schemas and the
> protocol revision may change between releases. Prefer [`cspark.sdk`](../sdk/) for
> stable Spark REST usage (execute, history, batches, etc.).

This module is a thin **MCP client** for Coherent's remote MCP server. It lets
Python agents and scripts call the same tools IDE connectors use (Cursor, Claude,
VS Code).

It does **not** start a local MCP server.

## Requirements

- Python **3.10+** (required by the `mcp` package)
- Optional extra: `pip install 'cspark[mcp]'`
- Bearer token or OAuth2 client credentials for a tenant where MCP is enabled
- Protocol support pinned to `mcp` **1.x** (`>=1.28,<2`) to match Coherent's current
  advertised revisions (`2024-11-05` and later). A future upgrade to `mcp` 2.x is
  planned when Coherent adopts the `2026-07-28` specification.

## Install

```bash
pip install 'cspark[mcp]'
```

## Connect to Coherent's MCP server

MCP URL shape:

```text
https://mcp.{environment}.coherent.global/{tenant}/mcp
```

Authentication for this client is **bearer token** or **OAuth2 client credentials**
(set `token=` / `CSPARK_BEARER_TOKEN`, or `oauth=` / env client credentials).
API key auth is not supported. Browser login belongs to IDE connectors, not this
module. When using OAuth2, the client retrieves an access token on connect.

```python
import asyncio
from cspark.mcp import AsyncMcpClient

async def main():
    async with AsyncMcpClient(env='my-env', tenant='my-tenant', token='...', logger=False) as mcp:
        tools = await mcp.list_tools()
        print([t['name'] for t in tools])

        info = await mcp.service_info(folder='my-folder', service='my-service')
        print(info)

asyncio.run(main())
```

Here's a [sample output](./sample.txt) of the example in the [examples/mcp_client.py](../../examples/mcp_client.py).

Synchronous wrapper (also a context manager):

```python
from cspark.mcp import McpClient

with McpClient(env='my-env', tenant='my-tenant', token='...', logger=False) as mcp:
    tools = mcp.list_tools()
    result = mcp.execute_v3(folder='my-folder', service='my-service', request_payload={'inputs': {'value': 42}})
    print(result)
```

You can also pass a full MCP URL via `base_url=`, or a SaaS Spark URL /
`BaseUrl`; `McpUrl` subclasses `BaseUrl` and converts via `to('mcp')`.
The connectable endpoint is `mcp_url.full` (includes `/{tenant}/mcp`).

## API surface

| Method | MCP tool |
| --- | --- |
| `list_tools()` | (session) |
| `call_tool(name, arguments)` | any tool by name |
| `execute_v3(...)` | `spark_execute_v3` |
| `service_info(...)` | `spark_service_info` |
| `generate_snippet(...)` | `spark_generate_snippet` |
| `compare_service_versions(...)` | `spark_compare_service_versions` |
| `download_api_history(...)` | `spark_download_api_history` |
| `download_testbed_template(...)` | `spark_download_testbed_template` |
| `download_testbed_result(...)` | `spark_download_testbed_result` |
| `list_testbeds(...)` | `spark_list_testbeds` |
| `list_testbed_results(...)` | `spark_list_testbed_results` |
| `run_testbed(...)` | `spark_run_testbed` |
| `run_status_testbed(...)` | `spark_run_status_testbed` |
| `compare_testbed_results(...)` | `spark_compare_testbed_results` |

Helpers accept snake_case Python kwargs and pass the documented MCP argument
keys through (for example `request_payload` → `requestPayload`).

## When to use `cspark.sdk` instead

Use the REST SDK when you need typed, stable APIs for execute, folders, services,
batches, ImpEx, or history. Use `cspark.mcp` when you need MCP tool parity for
agent frameworks or capabilities that are only exposed on the MCP server today
(for example Testing Center helpers).
