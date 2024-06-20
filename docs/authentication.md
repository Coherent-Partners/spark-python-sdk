# Authentication

The SDK supports three types of authentication schemes:

- `apiKey`
- `token`
- `oauth` (recommended method for production)

## API Key

A Spark API key is a synthetic key that allows you to authenticate to the platform
and access the following APIs:

- [Batch APIs][batch-apis]
- [Execute API][execute-api]
- [Metadata API][metadata-api]
- [Validation API][validation-api]

If and when you need that API key to access additional APIs, you need to review and
configure [feature permissions][feature-permissions] in the Spark platform. Find
out more on how to generate and manage API keys in the [Spark documentation][spark-api-keys].

Keep in mind that API keys are sensitive and should be kept secure. Therefore, we
strongly recommend reading [this article][openai-api-keys] by OpenAI on best practices
for API key safety.

To create a `Spark.Client()` instance with an API key, you can provide the key
directly as shown below:

```py
spark = Spark.Client(api_key='my-api-key')
```

When accessing publicly available APIs, you do not require an API key or any
other authentication mechanism. In fact, you can create a `Spark.Client` instance
without providing any authentication mechanism by setting the `api_key` to `open`:

```py
spark = Spark.Client(api_key='open')
```

> [!WARNING]
> You will not be able to read that API key later from the `Spark.Client` instance
> if needed. It's masked for security reasons.

```py
spark = Spark.Client(api_key='my-api-key')

# the client options are available in the `config`uration property
print(spark.config.auth.api_key) // '****-key'
```

## Bearer Token

A bearer token (or simply token) is a short-lived JSON Web token (JWT) that allows you
to authenticate to the Spark platform and access its APIs. Follow [this guide][bearer-token] to
learn how to access your bearer token.

Keep in mind that a bearer token is usually prefixed with 'Bearer'. However, the
SDK will automatically add the prefix if it is not provided. You can provide a bearer
token directly or set it in the environment variable `CSPARK_BEARER_TOKEN`.

```py
spark = Spark.Client(token='Bearer my-access-token')
```

## Client Credentials Grant

The [OAuth2.0 client credentials grant][oauth2] is the preferred scheme to handle
user authentication and authorization in the Spark platform. To use this grant,
you need to provide the client ID and secret or the path to the JSON file containing
the credentials.

Using the client ID and secret directly:

```py
spark = Spark.Client(oauth={'client_id': 'my-client-id', 'client_secret': 'my-client-secret'})
```

Alternatively, you can provide the path to the JSON file containing the client ID
and secret:

```py
spark = Spark.Client(oauth='path/to/my/credentials.json')
```

## Using Environment Variables (recommended)

As you already guess, the SDK will attempt to read the API key, bearer token, and
OAuth credentials from the environment variables. This is the recommended way to
store your sensitive information.

**Method 1**: Here's how you can export the environment variables in a Unix-like shell:

```bash
export CSPARK_BASE_URL='https://excel.my-env.coherent.global/my-tenant'
# and
export CSPARK_API_KEY='my-api-key'
# or
export CSPARK_BEARER_TOKEN='Bearer my-access-token'
# or
export CSPARK_CLIENT_ID='my-client-id'
export CSPARK_CLIENT_SECRET='my-client-secret'
# or
export CSPARK_OAUTH_PATH='path/to/my/client-credentials.json'
```

**Method 2** (preferred): Alternatively, you can use a `.env` file to store your
environment variables and use a library like [python-dotenv](https://pypi.org/project/python-dotenv/)
to load them into your application.

> [!WARNING]
> Please note that you should avoid committing your `.env` file to your repository
> to prevent exposing your sensitive information.

Creating a `Spark.Client` instance now becomes as simple as:

```py
spark = new Spark.Client()
```

## Good to know

When using the OAuth2.0 client credentials grant, the SDK will automatically refresh
the token when it expires. However, you can also generate or refresh the token manually. Here's
how you can do it:

```py
spark = Spark.Client(oauth='path/to/my/credentials.json')
spark.config.auth.oauth.retrieve_token(spark.config) # also return `AccessToken` object.

# the access token is now available in the configuration
print(f'access token: {spark.config.auth.oauth.access_token}')
```

If more than one authentication mechanisms are provided, the SDK will prioritize in
the following order: API key > Bearer token > and OAuth2.0 client credentials grant.

[batch-apis]: https://docs.coherent.global/spark-apis/batch-apis
[execute-api]: https://docs.coherent.global/spark-apis/execute-api
[metadata-api]: https://docs.coherent.global/spark-apis/metadata-api
[validation-api]: https://docs.coherent.global/spark-apis/validation-api
[feature-permissions]: https://docs.coherent.global/spark-apis/authorization-api-keys/permissions-features-permissions
[openai-api-keys]: https://help.openai.com/en/articles/5112595-best-practices-for-api-key-safety
[spark-api-keys]: https://docs.coherent.global/spark-apis/authorization-api-keys
[bearer-token]: https://docs.coherent.global/spark-apis/authorization-bearer-token
[oauth2]: https://docs.coherent.global/spark-apis/authorization-client-credentials
