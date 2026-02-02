from .._base import Uri
from .._oauth2 import AccessToken
from ._base import AsyncApiResource

__all__ = ['AsyncOAuth2']


class AsyncOAuth2(AsyncApiResource):
    async def gen_access_token(self):
        url = Uri.of(base_url=self.config.base_url.oauth2, version='protocol', endpoint='openid-connect/token')
        body = {**self.config.auth.oauth.to_dict(), 'grant_type': self.config.auth.oauth.flow}  # type: ignore

        return await self.request(url, method='POST', form=body)

    async def get_access_token(self) -> AccessToken:
        """Retrieves the access token from the OAuth2 server."""
        response = await self.gen_access_token()
        return AccessToken.from_dict(response.data)
