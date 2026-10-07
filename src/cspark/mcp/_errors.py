from __future__ import annotations

from typing import Any, Optional

from cspark.sdk import SparkSdkError
from cspark.sdk._errors import ErrorMessage

__all__ = ['SparkMcpError']


class SparkMcpError(SparkSdkError):
    """Raised when an MCP session or tool call fails."""

    def __init__(self, message: str, cause: Optional[Any] = None):
        super().__init__(ErrorMessage(message, cause))
