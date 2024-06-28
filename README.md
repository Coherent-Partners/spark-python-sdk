# Coherent Spark Python SDK

The Coherent Spark Python SDK (currently in Beta) is designed to elevate the developer
experience and provide a convenient access to the Coherent Spark APIs.

👋 **Just a heads-up:**

This SDK is supported by the community. If you encounter any bumps while using it,
please report them [here](https://github.com/c-spark/spark-py-sdk/issues)
by creating a new issue.

> **Note:** Currently being developed. Please check back soon for updates.

## Installation

```bash
pip install -U cspark
```

> 🫣 This Python library requires [Python 3.7+](https://www.python.org/downloads/).

## Usage

To use the SDK, you need a Coherent Spark account that lets you access the following:

- User authentication ([API key][api-key-docs], [bearer token][bearer-token-docs]
  or [OAuth2.0 client credentials][oauth2-docs] details)
- Base URL (including the environment and tenant name)
- Spark service URI (to locate a specific resource):
  - `folder` - the folder name (where the service is located)
  - `service` - the service name
  - `version` - the semantic version a.k.a revision number (e.g., 0.4.2)

A `folder` contains one or more `service`s, and a `service` can have
multiple `version`s. Technically speaking, when you're operating with a service,
you're actually interacting with a specific version of that service (the latest
version by default - unless specified otherwise).

Hence, there are various ways to indicate a Spark service URI:

- `{folder}/{service}[?{version}]` - _version_ is optional.
- `service/{serviceId}`
- `version/{versionId}`

> **IMPORTANT:** Avoid using URL-encoded characters in the service URI.

Here's an example of how to execute a Spark service:

```py
import cspark.sdk as Spark

spark = Spark.Client(env='my-env', tenant='my-tenant', api_key='my-api-key')
with spark.services as services:
    response = services.execute('my-folder/my-service', inputs={'value': 42})
    print(response.data)
```

Explore the [examples](./examples/main.py) and [documentation](./docs) folders
to find out more about the SDK's capabilities.

## Client Options

As shown in the examples above, the `Spark.Client` is your entry point to the SDK.
It is quite flexible and can be configured with the following options:

### Base URL

`base_url` (default: `os.getenv['CSPARK_BASE_URL']`): indicates the base URL of
the Coherent Spark APIs. It should include the tenant and environment information.

```py
spark = Spark.Client(base_url='https://excel.my-env.coherent.global/my-tenant')
```

Alternatively, a combination of `env` and `tenant` options can be used to construct
the base URL.

```py
spark = Spark.Client(env='my-env', tenant='my-tenant')
```

### Authentication

The SDK supports three types of authentication mechanisms:

- `api_key` (default: `os.getenv['CSPARK_API_KEY']`): indicates the API key
  (also known as synthetic key), which is sensitive and should be kept secure.

```py
spark = Spark.Client(api_key='my-api-key')
```

> **PRO TIP:**
> The Spark platform supports public APIs that can be accessed without any form
> of authentication. In that case, you need to set `api_key` to `open` in order to
> create a `Spark.Client`.

- `token` (default: `os.getenv['CSPARK_BEARER_TOKEN']`): indicates the bearer token.
  It can be prefixed with 'Bearer' or not. A bearer token is usually valid for a
  limited time and should be refreshed periodically.

```py
spark = Spark.Client(token='Bearer 123')
```

- `oauth` (default: `os.getenv['CSPARK_CLIENT_ID']` and `os.getenv['CSPARK_CLIENT_SECRET']` or
  `os.getenv['CSPARK_OAUTH_PATH']`): indicates the OAuth2.0 client credentials.
  You can either provide the client ID and secret directly or provide the file path
  to the JSON file containing the credentials.

```py
spark = Spark.Client(oauth={ client_id: 'my-client-id', client_secret: 'my-client-secret' })
# or
spark = Spark.Client(oauth='path/to/oauth/credentials.json')
```

- `timeout` (default: `60000`): indicates the maximum amount of time (in milliseconds)
  that the client should wait for a response from Spark servers before timing out a request.

- `max_retries` (default: `2`): indicates the maximum number of times that the client
  will retry a request in case of a temporary failure, such as a unauthorized
  response or a status code greater than 400.

- `retry_interval` (default: `1` second): indicates the delay between each retry.

- `logger` (default: `True`): enables or disables logs for the SDK.

```py
spark = Spark.Client(logger=False)
```

## Client Errors

`SparkError` is the base class for all custom errors thrown by the SDK. There are
two types of it:

- `SparkSdkError`: usually thrown when an argument (user entry) fails to comply
  with the expected format. Because it's a client-side error, it will include in
  the majority of cases the invalid entry as `cause`.
- `SparkApiError`: when attempting to communicate with the API, the SDK will wrap
  any sort of failure (any error during the roundtrip) into `SparkApiError`, which
  includes the HTTP `status` code of the response and the `request_id`, a unique
  identifier of the request.

Some of the derived `SparkApiError` are:

| Type                      | Status      | When                           |
| ------------------------- | ----------- | ------------------------------ |
| `InternetError`           | 0           | no internet access             |
| `BadRequestError`         | 400         | invalid request                |
| `UnauthorizedError`       | 401         | missing or invalid credentials |
| `ForbiddenError`          | 403         | insufficient permissions       |
| `NotFoundError`           | 404         | resource not found             |
| `ConflictError`           | 409         | resource already exists        |
| `RateLimitError`          | 429         | too many requests              |
| `InternalServerError`     | 500         | server-side error              |
| `ServiceUnavailableError` | 503         | server is down                 |
| `UnknownApiError`         | `undefined` | unknown error                  |

## API Parity

The SDK aims to provide over time full parity with the Spark APIs. Below is a list
of the currently supported APIs.

[Authentication API](./docs/authentication.md) - manages access tokens using
OAuth2.0 Client Credentials flow:

- `Authorization.oauth.retrieve_token(config)` generates new access token.

[Service API](./docs/services.md) - manages Spark services:

- `Spark.services.execute(uri, inputs)` executes a Spark service.
- `Spark.services.get_versions(uri)` lists all the versions of a service.
- `Spark.services.get_schema(uri)` gets the schema of a service.
- `Spark.services.get_metadata(uri)` gets the metadata of a service.

> **PRO TIP:**
> A service URI locator can be combined with other parameters to locate a specific
> service (or version of it) when it's not a string. For example, you may execute
> a public service using an object containing the `folder`, `service`, and `public`
> properties.

```py
import cspark.sdk as Spark

spark = Spark.Client(env='my-env', tenant='my-tenant', api_key='open')

with spark.services as services:
    uri = Spark.UriParams(folder='my-folder', service='my-service', public=True)
    response = services.execute(uri, inputs={ 'value': 42 })
    print(response.data)

# The final URI in this case is:
#    'my-tenant/api/v3/public/folders/my-folder/services/my-service/execute'
```

See the [Uri and UriParams](./src/cspark/sdk/resources/_base.py) class for more details.

## Contributing

Feeling motivated enough to contribute? Great! Your help is always appreciated.

Please read [CONTRIBUTING.md](./CONTRIBUTING.md) for details on the code of
conduct, and the process for submitting pull requests.

## Copyright and License

[Apache-2.0](./LICENSE)

[api-key-docs]: https://docs.coherent.global/spark-apis/authorization-api-keys
[bearer-token-docs]: https://docs.coherent.global/spark-apis/authorization-bearer-token
[oauth2-docs]: https://docs.coherent.global/spark-apis/authorization-client-credentials
