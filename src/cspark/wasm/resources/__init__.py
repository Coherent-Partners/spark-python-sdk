from ._async import *
from ._base import *
from ._services import *

__all__ = ['Version', 'Health', 'Status']


class Version(HybridResource):
    def get(self):
        return self.request(f'{self.config.base_url.value}/version')


class Health(HybridResource):
    def check(self):
        return self.request(f'{self.config.base_url.value}/healthcheck')


class Status(HybridResource):
    def get(self):
        return self.request(f'{self.config.base_url.value}/status')
