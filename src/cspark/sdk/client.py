from __future__ import annotations

import cspark.sdk.resources as API

from .config import Config

__all__ = ['Client']


class Client:
    def __init__(self, config: Config) -> None:
        self.config = config

    @property
    def service(self) -> API.Service:
        return API.Service(self.config)
