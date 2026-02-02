from ._base import AsyncApiResource

__all__ = ['AsyncHealth', 'AsyncPlatform']


class AsyncHealth(AsyncApiResource):
    async def check(self):
        """Checks the health status or connectivity of a Spark environment."""
        return await self.request(f'{self.config.base_url.value}/health', method='GET')

    async def ok(self) -> bool:
        """Returns `True` if the Spark environment is healthy."""
        response = await self.check()
        status = response.data.get('status', '').lower() if isinstance(response.data, dict) else ''
        return response.status == 200 and status == 'up'


class AsyncPlatform(AsyncApiResource):
    async def get_config(self):
        """Returns Spark configuration for the current user."""
        url = f'{self.config.base_url.value}/api/v1/config/GetSparkConfiguration'
        response = await self.request(url, method='GET')
        if isinstance(response.data, dict) and response.data.get('status') == 'Success':
            return response.copy_with(data=response.data.get('data'))
        return response
