from __future__ import annotations

from typing import Dict, Generic, Mapping, Optional, TypeVar

TReq = TypeVar('TReq')
TResp = TypeVar('TResp')
Headers = Dict[str, str] | Mapping[str, str]


class TRequest(Generic[TReq]):
    def __init__(self, url: str, method: str, headers: Headers, body: Optional[TReq]):
        self.url = url
        self.method = method
        self.headers = headers
        self.body = body


class TResponse(Generic[TResp]):
    def __init__(self, headers: Headers, body: TResp, raw: str):
        self.headers = headers
        self.body = body
        self.raw = raw
