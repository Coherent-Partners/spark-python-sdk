from dataclasses import dataclass
from typing import Any, Union

from ._base import ApiResource, Uri

__all__ = ['OAuth2', 'AccessToken']


class OAuth2(ApiResource):
    def gen_access_token(self):
        url = Uri.of(base_url=self.config.base_url.oauth2, version='protocol', endpoint='openid-connect/token')
        body = {**self.config.auth.oauth.to_dict(), 'grant_type': self.config.auth.oauth.flow}  # type: ignore

        return self.request(url, method='POST', form=body)

    def get_access_token(self) -> 'AccessToken':
        """Retrieves the access token from the OAuth2 server."""
        response = self.gen_access_token()
        return AccessToken.from_dict(response.data)


@dataclass(frozen=True)
class AccessToken:
    access_token: str
    expires_in: int
    refresh_expires_in: int
    token_type: str
    not_before_policy: int
    scope: str

    @staticmethod
    def from_dict(data: Union[None, Any, str]) -> 'AccessToken':
        if not isinstance(data, dict):
            data = {}

        return AccessToken(
            access_token=str(data.get('access_token', '')),
            expires_in=int(data.get('expires_in', 0)),
            refresh_expires_in=int(data.get('refresh_expires_in', 0)),
            token_type=str(data.get('token_type', '')),
            not_before_policy=int(data.get('not-before-policy', 0)),
            scope=str(data.get('scope', '')),
        )
