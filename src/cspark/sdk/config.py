from __future__ import annotations

import json
from typing import Optional
from urllib.parse import urlparse

from .errors import SparkError
from .utils import is_str_empty
from .validators import Validators

__all__ = ['BaseUrl']


class Config:
    pass


class BaseUrl:
    def __init__(self, *, url: Optional[str] = None, tenant: Optional[str] = None, env: Optional[str] = None):
        base_url, tenant_name = self._parse(url=url, tenant=tenant, env=env)
        self._base: str = base_url
        self._tenant: str = tenant_name

    @property
    def tenant(self) -> str:
        return self._tenant

    @property
    def full(self) -> str:
        return f'{self._base}/{self._tenant}'

    @property
    def value(self) -> str:
        return self._base

    @property
    def oauth2(self) -> str:
        return f'{self.to("keycloak")}/auth/realms/{self._tenant}'

    def to(self, service: str = 'excel', with_tenant: bool = False) -> str:
        return (self.full if with_tenant else self.value).replace('excel', service)

    def _parse(
        self, url: Optional[str] = None, tenant: Optional[str] = None, env: Optional[str] = None
    ) -> tuple[str, str]:
        str_validator = Validators.empty_str()
        url_validator = Validators.base_url()

        if url_validator.is_valid(url):
            _url = urlparse(url)
            paths = str(_url.path).split('/')
            _tenant = paths[1] if len(paths) > 1 else tenant

            if str_validator.is_valid(_tenant, 'tenant name is required'):
                base_url = f'{_url.scheme}://{_url.netloc}'
                return base_url, str(_tenant)
        elif not is_str_empty(tenant) and not is_str_empty(env):
            _tenant = str(tenant).strip().lower()
            _base_url = f'https://excel.{str(env).strip().lower()}.coherent.global'
            return _base_url, _tenant
        else:
            # capture errors for missing parameters
            str_validator.is_valid(env, 'environment name is missing') and str_validator.is_valid(
                tenant, 'tenant name is missing'
            )  # pyright: ignore[reportUnusedExpression]

        errors = url_validator.errors + str_validator.errors
        raise SparkError.sdk(
            message='; '.join(e.message for e in errors)
            if len(errors) > 0
            else 'cannot build base URL from invalid parameters',
            cause=json.dumps({'url': url, 'tenant': tenant, 'env': env}),
        )
