"""
Coherent MCP client.

Connects to Coherent's remote MCP server so Python agents and scripts can invoke
the same tools exposed to IDE clients (Cursor, Claude, VS Code).

Requires the optional extra::

    pip install 'cspark[mcp]'

Python 3.10+ is required by the ``mcp`` dependency. Prefer ``cspark.sdk`` for
normal Spark REST usage.
"""

from ._client import *
from ._config import *
from ._errors import *

__all__ = [
    'AsyncMcpClient',
    'McpClient',
    'McpConfig',
    'McpUrl',
    'SparkMcpError',
]
