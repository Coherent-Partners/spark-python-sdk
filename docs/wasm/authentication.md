# Authentication

By default, Hybrid Runners do not require authentication. However, you may use the
following security schemes for particular use cases:

- [API key](#api-key)
- [Bearer token](#bearer-token)

## Open Authentication

When you don't need to authenticate, you must set the `token` or `api_key` to `open`.
Otherwise, the SDK will throw an error as authentication is a strict requirement.

## API Key

A Spark API key is a synthetic key that allows you to authenticate to the SaaS platform
and can be used for hybrid deployments relying on the [Automatic Wasm Pull][user-guide]
method.

To create a `Hybrid.Client` instance with an API key, you can provide the key
directly or set it in the environment variable `CSPARK_API_KEY`:

```python
import cspark.wasm as Hybrid

hybrid = Hybrid.Client(api_key='my-api-key')
```

## Bearer Token

A bearer token (or simply token) is a short-lived JSON Web token (JWT) that allows you
to authenticate to the Spark platform and access its APIs. Follow [this guide][bearer-token] to
learn how to access your bearer token.

Sometimes, a bearer token is prefixed with the word 'Bearer'. But the SDK will know
how to handle it whether you choose it to prefix your token or not. You can set a
token directly or define it in the environment variable `CSPARK_BEARER_TOKEN`.

```python
import cspark.wasm as Hybrid

hybrid = Hybrid.Client(token='Bearer my-access-token')  # with prefix
# or
hybrid = Hybrid.Client(token='my-access-token')  # without prefix
```

## Good to Know

The API keys do not authenticate against the Hybrid Runner API per se; they're used
to authenticate against the SaaS platform to access WebAssembly packages and download
them to the runner when necessary.

> [!NOTE]
> If you need to authenticate against the Hybrid Runner API, you will need to define
> and use your own security layer such as API Management.

If your runner is deployed in a private network or airgap environment and has no
access to the internet, the runner will not be able to function properly.

[Back to top](#authentication)

[user-guide]: https://docs.coherent.global/hybrid-runner/introduction-to-the-hybrid-runner
[bearer-token]: https://docs.coherent.global/spark-apis/authorization-bearer-token
