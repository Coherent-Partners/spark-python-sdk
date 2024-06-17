from dataclasses import dataclass
from typing import Dict, cast

from .._config import Config
from ._base import ApiResource, Uri

__all__ = ['OAuth2', 'AccessToken']


class OAuth2(ApiResource):
    def __init__(self, config: Config):
        super().__init__(config)

    def get_access_token(self) -> 'AccessToken':
        url = Uri.of(base_url=self.config.base_url.oauth2, version='protocol', endpoint='openid-connect/token')
        body = {**self.config.auth.oauth.to_dict()}  # pyright: ignore[reportOptionalMemberAccess]
        body['grant_type'] = self.config.auth.oauth.flow  # pyright: ignore[reportOptionalMemberAccess]

        response = self.request(url, method='POST', form=body)
        data = cast(Dict, response.data)
        return AccessToken(
            access_token=str(data.get('access_token', '')),
            expires_in=int(data.get('expires_in', 0)),
            refresh_expires_in=int(data.get('refresh_expires_in', 0)),
            token_type=str(data.get('token_type', '')),
            not_before_policy=int(data.get('not-before-policy', 0)),
            scope=str(data.get('scope', '')),
        )


@dataclass(frozen=True)
class AccessToken:
    access_token: str
    expires_in: int
    refresh_expires_in: int
    token_type: str
    not_before_policy: int
    scope: str
