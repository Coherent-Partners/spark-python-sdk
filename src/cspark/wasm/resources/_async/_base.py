from cspark.sdk import AsyncApiResource

from ..._version import about

__all__ = ['AsyncHybridResource']


class AsyncHybridResource(AsyncApiResource):
    @property
    def default_headers(self):
        return {**super().default_headers, 'User-Agent': about}
