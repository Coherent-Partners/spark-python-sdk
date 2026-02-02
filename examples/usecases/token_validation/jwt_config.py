import re
from typing import Any, Mapping, Optional, Union
from urllib.parse import urlparse

import jwt  # type: ignore
from cspark.sdk import BaseUrl, Config, LoggerOptions, SparkError


class JwtConfig(Config):
    def __init__(
        self,
        token: str,
        *,
        verify: bool = True,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        retry_interval: Optional[float] = None,
        logger: Union[bool, Mapping[str, Any], LoggerOptions] = True,
    ):
        options = JwtConfig.decode(token, verify=verify)
        if verify and not options['verified']:
            raise SparkError.sdk(options['decoded'], cause=f'{options["token"][:32]}...')

        super().__init__(
            token=options['token'],
            base_url=options['base_url'],
            tenant=options['tenant'],
            timeout=timeout,
            max_retries=max_retries,
            retry_interval=retry_interval,
            logger=logger,
        )

    @staticmethod
    def decode(token: str, verify: bool = True) -> dict:
        valid, base_url, tenant = False, None, None
        token = re.sub(r'(?i)\bBearer\b', '', token).strip()

        try:
            decoded = jwt.decode(token, options={'verify_signature': False})
        except Exception as exc:
            decoded = f'invalid token ({exc})'
            return {'token': token, 'base_url': base_url, 'tenant': tenant, 'verified': valid, 'decoded': decoded}

        issuer = decoded.get('iss')
        if verify:
            valid, decoded = JwtConfig.validate(token, issuer)

        if isinstance(decoded, dict):
            url, tenant = urlparse(issuer), decoded.get('realm')
            base_url = BaseUrl.of(url=f'{url.scheme}://{url.netloc}', tenant=tenant).to('excel')
        return {'token': token, 'base_url': base_url, 'tenant': tenant, 'verified': valid, 'decoded': decoded}

    @staticmethod
    def validate(token: str, issuer: str, *, audience: str = 'product-factory', algorithms: tuple[str] = ('RS256',)):
        try:
            jwks_client = jwt.PyJWKClient(f'{issuer}/protocol/openid-connect/certs')
            signing_key = jwks_client.get_signing_key_from_jwt(token)
            decoded = jwt.decode(token, key=signing_key, algorithms=algorithms, audience=audience, issuer=issuer)
            return True, decoded
        except Exception as exc:
            return False, str(exc)


def main():
    TOKEN = 'eyJhbGciOiJIUzI1NiJ9.'  # this uses HS256 algorithm for testing but Coherent uses RS256 algorithm.
    TOKEN += 'eyJpc3MiOiJodHRwczovL2tleWNsb2FrLm15LWVudi5jb2hlcmVudC5nbG9iYWwvYXV0aC9yZWFsbXMvbXktdGVuYW50IiwicmVhbG0iOiJteS10ZW5hbnQifQ.'
    TOKEN += '9G0zF-XAN9EpDLu11tmqkRwNFU52ecoGz4vTq0NEJBw'
    config = JwtConfig.decode(TOKEN, verify=False)
    print(config)


if __name__ == '__main__':
    main()
