from .._config import Config
from ._base import ApiResource

__all__ = ['Batches']


class Batches(ApiResource):
    def __init__(self, config: Config):
        super().__init__(config)

    def create(self):
        pass

    def of(self, id: str):
        pass
