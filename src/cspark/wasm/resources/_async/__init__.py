from ._base import *
from ._services import *

__all__ = ['AsyncVersion', 'AsyncHealth', 'AsyncStatus', 'AsyncServices']


class AsyncVersion(AsyncHybridResource):
    async def get(self):
        return await self.request(f'{self.config.base_url.value}/version')


class AsyncHealth(AsyncHybridResource):
    async def check(self):
        return await self.request(f'{self.config.base_url.value}/healthcheck')


class AsyncStatus(AsyncHybridResource):
    async def get(self):
        return await self.request(f'{self.config.base_url.value}/status')
