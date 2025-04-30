from ._base import ApiResource

__all__ = ['Health']


class Health(ApiResource):
    def check(self):
        """Checks the health status or connectivity of a Spark environment."""
        return self.request(f'{self.config.base_url.value}/health', method='GET')

    def ok(self) -> bool:
        """Returns `True` if the Spark environment is healthy."""
        response = self.check()
        status = response.data.get('status', '').lower() if isinstance(response.data, dict) else ''
        return response.status == 200 and status == 'up'
