from cspark.sdk import ApiResource

from .._version import about

__all__ = ['HybridResource']


class HybridResource(ApiResource):
    @property
    def default_headers(self):
        return {**super().default_headers, 'User-Agent': about}
