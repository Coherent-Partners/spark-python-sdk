from __future__ import annotations

import json
import os
import re
from typing import Mapping, Optional, Union

from ._config import Config
from ._constants import ENV_VARS
from ._errors import SparkError
from ._logger import get_logger
from ._utils import StringUtils
from .resources import AccessToken
from .resources import OAuth2 as OAuthManager

__all__ = ['Authorization', 'OAuth']


class Authorization:
    _oauth: Optional['OAuth']

    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        token: Optional[str] = None,
        oauth: Union[None, Mapping[str, str], str] = None,
    ) -> None:
        client_id = os.getenv(ENV_VARS.CLIENT_ID)
        client_secret = os.getenv(ENV_VARS.CLIENT_SECRET)
        oauth_path = os.getenv(ENV_VARS.OAUTH_PATH)

        self._api_key = api_key
        self._token = re.sub(r'(?i)\bBearer\b', '', token).strip() if token else None
        if oauth:
            self._oauth = OAuth.when(oauth) if isinstance(oauth, (str, Mapping)) else None
        elif client_id and client_secret:
            self._oauth = OAuth({'client_id': client_id, 'client_secret': client_secret})
        elif oauth_path:
            self._oauth = OAuth.file(oauth_path)
        else:
            self._oauth = None

        if self.is_empty:
            raise SparkError.sdk(
                cause=json.dumps({'api_key': api_key, 'token': token, 'oauth': str(oauth)}),
                message='user authentication is required; '
                'provide a valid API key, bearer token, or OAuth credentials to proceed.\n'
                'If you will be fetching public APIs, set API key as "open".',
            )

    @property
    def is_open(self) -> bool:
        return self._api_key == 'open' or self._token == 'open'

    @property
    def is_empty(self) -> bool:
        return not self._api_key and not self._token and not self._oauth

    @property
    def api_key(self) -> Optional[str]:
        if self._api_key and not self.is_open:
            return StringUtils.mask(self._api_key)
        return self._api_key

    @property
    def token(self) -> Optional[str]:
        return self._token

    @property
    def oauth(self) -> Optional['OAuth']:
        return self._oauth

    @property
    def type(self) -> Optional[str]:
        return 'api_key' if self._api_key else 'token' if self._token else 'oauth' if self._oauth else None

    @property
    def as_header(self) -> Mapping[str, str]:
        if self._oauth:
            return {'Authorization': f'Bearer {self._oauth.access_token}'}
        if self._api_key and not self.is_open:
            return {'x-synthetic-key': self._api_key}
        if self._token and not self.is_open:
            return {'Authorization': f'Bearer {self._token}'}
        return {}


class OAuth:
    _access_token: Optional[AccessToken]

    def __init__(self, value: Mapping[str, str]) -> None:
        self._client_id = value.get('client_id', '')
        self._client_secret = value.get('client_secret', '')
        self._file_path: Optional[str] = value.get('oauth_path')
        self._access_token = None

        if 'client_id' not in value or 'client_secret' not in value:
            raise SparkError.sdk(
                cause=json.dumps(value),
                message='invalid authorization properties. '
                'Provide a JSON object including cliend_id and client_secret '
                'or a path to a JSON file containing the client ID and secret.',
            )

    @staticmethod
    def when(value: Union[Mapping[str, str], str]) -> 'OAuth':
        if isinstance(value, str):
            return OAuth.file(value)
        return OAuth(value)

    @staticmethod
    def file(path: str) -> 'OAuth':
        try:
            with open(path) as file:
                creds = json.load(file)
        except Exception as cause:
            raise SparkError.sdk(f'failed to create oauth credentials from file <{path}>', cause=cause) from cause
        return OAuth({**creds, 'oauth_path': path})

    def __str__(self) -> str:
        return json.dumps(
            {
                'client_id': self._client_id,
                'client_secret': self.client_secret,
                'access_token': self.access_token,
            }
        )

    @property
    def access_token(self) -> Optional[str]:
        return self._access_token.access_token if self._access_token else None

    @property
    def client_id(self) -> str:
        return self._client_id

    @property
    def client_secret(self) -> str:
        return StringUtils.mask(self._client_secret)

    @property
    def version(self) -> str:
        return '2.0'

    @property
    def flow(self) -> str:
        return 'client_credentials'

    def to_dict(self) -> Mapping[str, str]:
        return {'client_id': self._client_id, 'client_secret': self._client_secret}

    def retrieve_token(self, config: Config) -> AccessToken:
        logger = get_logger(**config.logger.__dict__)

        try:
            with OAuthManager(config) as manager:
                logger.info('retrieving OAuth2 access token...')
                self._access_token = manager.get_access_token()
                if not self._access_token:
                    raise SparkError('no access token found')
                return self._access_token
        except Exception as cause:
            error = SparkError('failed to retrieve OAuth2 access token', cause)
            logger.warning(error.message)
            raise error from cause
