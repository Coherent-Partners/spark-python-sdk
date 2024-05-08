from ..config import Config

__all__ = ['ApiResource']


class ApiResource:
    def __init__(self, config: Config):
        self.config = config
