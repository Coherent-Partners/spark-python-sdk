"""
Experimental example: list Coherent MCP tools and fetch service info.

Requires:
  pip install 'cspark[mcp]'   # or: rye sync --features mcp
  CSPARK_BEARER_TOKEN, and either CSPARK_BASE_URL or CSPARK_ENV + CSPARK_TENANT

Important: do not name this file ``mcp.py`` — that shadows the third-party ``mcp``
package on ``sys.path`` and breaks imports.
"""

import asyncio

from cspark.mcp import AsyncMcpClient
from cspark.sdk import SparkError
from dotenv import load_dotenv


async def main() -> None:
    async with AsyncMcpClient(logger=False) as mcp:
        tools = await mcp.list_tools()
        print(f'connected to MCP server at {mcp.config.base_url.full}')
        print(f'tools ({len(tools)}):')
        for tool in tools:
            print(f'  - {tool["name"]}: {tool.get("description") or ""}')

        info = await mcp.service_info(folder='my-folder', service='my-service')
        print('service_info:', info)


if __name__ == '__main__':
    load_dotenv()
    try:
        asyncio.run(main())
    except SparkError as err:
        print(err.message)
        print(err.details)
    except Exception as exc:
        print(f'Unknown error: {exc}')
