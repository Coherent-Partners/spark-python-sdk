from .._config import Config
from ._base import ApiResource


class Services(ApiResource):
    def __init__(self, config: Config):
        super().__init__(config)

    def execute(self):
        pass

    def close(self):
        super().close()
