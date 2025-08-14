from cspark.sdk import ApiResource

from ._services import *

__all__ = ['Version', 'Health', 'Status']


class Version(ApiResource):
    def get(self):
        return self.request(f'{self.config.base_url.value}/version')


class Health(ApiResource):
    def check(self):
        return self.request(f'{self.config.base_url.value}/healthcheck')


class Status(ApiResource):
    def get(self):
        return self.request(f'{self.config.base_url.value}/status')
