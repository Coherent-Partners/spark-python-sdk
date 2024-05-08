from ..config import Config
from .base import ApiResource


class Service(ApiResource):
    def __init__(self, config: Config):
        super().__init__(config)
