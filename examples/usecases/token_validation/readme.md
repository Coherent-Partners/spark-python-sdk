## Validate JWTs against Keycloak

This example demonstrates how to decode and validate JSON web tokens (JWT) or bearer
tokens issued by [Keycloak].

Keycloak is the identity and access management solution used by Coherent Spark to
secure its services. It issues JWTs that can be used to authenticate and authorize
requests to the services.

There are scenarios such as [Xconnector] where you need to implement a remote service
that requires a bearer token to be passed in the request header. In order to trust
that token, you need to validate its signature against the Keycloak server before
proceeding with the request.

## Setup and Testing

To test this example, grab a JWT (without the prefix `Bearer`) issued by Keycloak
and modify the `TOKEN` variable in [main.py](main.py) with the JWT. Then, run the
following command:

```bash
poetry run python main.py
```

The script will decode the JWT using [pyjwt] and validate its signature against
Spark's Keycloak server. If and when the token is valid, `validate_token()` returns
a tuple that includes the validation status (i.e.,`True`) and the decoded token as
a dictionary.

## Extending the SDK Configuration

It should be noticed that the JWT value carries lots of information about the user and
the application once decoded. Part of this information includes `base_url` and `tenant`
that can be used to create a `Spark.Client` instance.

So, by extending the `Spark.Config` class (e.g., [JwtConfig](jwt_config.py)) to decode
and extract `base_url` and `tenant` from the JWT, these can be used along with the JWT
value to configure the SDK and create a `Spark.Client` instance.

For example, the following code shows how to decode a JWT and extract `base_url` and
`tenant` from it:

```python
> from jwt_config import JwtConfig # located in jwt_config.py
> TOKEN = 'eyJhbGciOiJIUzI1NiJ9.'  # this uses HS256 algorithm for testing but Spark uses RS256 algorithm.
> TOKEN += 'eyJpc3MiOiJodHRwczovL2tleWNsb2FrLm15LWVudi5jb2hlcmVudC5nbG9iYWwvYXV0aC9yZWFsbXMvbXktdGVuYW50IiwicmVhbG0iOiJteS10ZW5hbnQifQ.'
> TOKEN += '9G0zF-XAN9EpDLu11tmqkRwNFU52ecoGz4vTq0NEJBw'
>
> decoded = JwtConfig.decode(TOKEN, verify=False) # As this token is not signed by Keycloak, it can't be verified.
> print(decoded)
{'token':'eyJhbGciOiJIUzI1NiJ9...', 'base_url':'https://excel.my-env.coherent.global', 'tenant':'my-tenant', 'verified':False, 'decoded':{...}}
```

This plays well with extended [Spark.ApiResource][api-resource] as it can be used
as a `Spark.Config` instance when creating custom API resources to support addtional
API endpoints the SDK doesn't support yet.

```py
from cspark.sdk import ApiResource
from jwt_config import JwtConfig # located in jwt_config.py

class ExtendedResource(ApiResource):
    def fetch_data(self):
        return self.request(f'{self.config.base_url.value}/api/v1/my/resource', method='GET')

config = JwtConfig('Bearer my-access-token')
with ExtendedResource(config) as resource:
    response = resource.fetch_data()
print(response.data)
```

> Note that implementations like the one above are rare use cases. And it's OK to
> implement them as long as you understand what you're doing.
> Also, remember that [PyJWT][pyjwt] library must be installed to use this example.

<!-- References -->
[Keycloak]: https://www.keycloak.org/
[xconnector]: https://docs.coherent.global/xconnector/introduction-to-xconnector
[pyjwt]: https://pyjwt.readthedocs.io/en/stable/usage.html#encoding-decoding-tokens-with-rs256-rsa
[api-resource]: https://github.com/Coherent-Partners/spark-python-sdk/blob/main/docs/readme.md#api-resource
