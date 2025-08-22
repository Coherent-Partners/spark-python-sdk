from ._base import ApiResource

__all__ = ['Health', 'Platform']


class Health(ApiResource):
    def check(self):
        """Checks the health status or connectivity of a Spark environment."""
        return self.request(f'{self.config.base_url.value}/health', method='GET')

    def ok(self) -> bool:
        """Returns `True` if the Spark environment is healthy."""
        response = self.check()
        status = response.data.get('status', '').lower() if isinstance(response.data, dict) else ''
        return response.status == 200 and status == 'up'


class Platform(ApiResource):
    def get_config(self):
        """Returns Spark configuration for the current user."""
        url = f'{self.config.base_url.value}/api/v1/config/GetSparkConfiguration'
        response = self.request(url, method='GET')
        if isinstance(response.data, dict) and response.data.get('status') == 'Success':
            return response.copy_with(data=response.data.get('data'))
        return response
