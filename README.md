# Coherent Spark Python SDK

[![PyPI version][version-img]][version-url]

The Coherent Spark Python SDK (currently in **Beta**) is designed to elevate the developer
experience and provide convenient access to Coherent Spark APIs.

👋 **Just a heads-up:**

This SDK is supported by the community. If you encounter any bumps while using it,
please report them [here](https://github.com/Coherent-Partners/spark-python-sdk/issues)
by creating a new issue.

## Installation

```bash
pip install cspark # or pip install 'cspark[cli]' for CLI support.
```

> 🫣 This Python library requires [Python 3.7+](https://www.python.org/downloads/).

## Usage

To use the SDK, you need a Coherent Spark account that lets you access the following:

- User authentication ([API key][api-key-docs], [bearer token][bearer-token-docs],
  or [OAuth2.0 client credentials][oauth2-docs] details)
- Base URL (including the environment and tenant name)
- Spark service URI (to locate a specific resource):
  - `folder` - the folder name (where the service is located)
  - `service` - the service name
  - `version` - the semantic version a.k.a revision number (e.g., 0.4.2)

A `folder` contains one or more `service`s, which can have multiple `version`s.
Technically speaking, when you're operating with a service, you're actually
interacting with a specific version of that service (the latest version by default -
unless specified otherwise).

Hence, there are various ways to indicate a Spark service URI:

- `{folder}/{service}[?{version}]` - _version_ is optional.
- `service/{service_id}`
- `version/{version_id}`

> **IMPORTANT:** Avoid using URL-encoded characters in the service URI.

Here's an example of how to execute a Spark service:

```py
import cspark.sdk as Spark

spark = Spark.Client(env='my-env', tenant='my-tenant', api_key='my-api-key')
with spark.services as services:
    response = services.execute('my-folder/my-service', inputs={'value': 42})
    print(response.data)
```

Explore the [examples] and [documentation] folders to find out more about the SDK's capabilities.

> **PRO TIP:**
> A service URI locator can be combined with other parameters to locate a specific
> service (or version of it) when it's not a string. For example, you may execute
> a public service using a `UriParams` object by specifying the `folder`, `service`,
> and `public` properties.

```py
import cspark.sdk as Spark

spark = Spark.Client(env='my-env', tenant='my-tenant', api_key='open')

with spark.services as services:
    uri = Spark.UriParams(folder='my-folder', service='my-service', public=True)
    response = services.execute(uri, inputs={'value': 42})
    print(response.data)

# The final URI in this case is:
#    'my-tenant/api/v3/public/folders/my-folder/services/my-service/execute'
```

See the [Uri and UriParams](./src/cspark/sdk/resources/_base.py) classes for more details.

## Client Options

As shown in the examples above, the `Spark.Client` is your entry point to the SDK.
It is quite flexible and can be configured with the following options:

### Base URL

`base_url` (default: `os.getenv['CSPARK_BASE_URL']`) indicates the base URL of
Coherent Spark APIs. It should include the tenant and environment information.

```py
spark = Spark.Client(base_url='https://excel.my-env.coherent.global/my-tenant')
```

Alternatively, a combination of `env` and `tenant` options can be used to construct
the base URL.

```py
spark = Spark.Client(env='my-env', tenant='my-tenant')
```

### Authentication

The SDK supports three types of authentication schemes:

- `api_key` (default: `os.getenv['CSPARK_API_KEY']`) indicates the API key
  (also known as synthetic key), which is sensitive and should be kept secure.

```py
spark = Spark.Client(api_key='my-api-key')
```

> **PRO TIP:**
> The Spark platform supports public APIs that can be accessed without any form
> of authentication. In that case, you need to set `api_key` to `open` in order to
> create a `Spark.Client`.

- `token` (default: `os.getenv['CSPARK_BEARER_TOKEN']`) indicates the bearer token.
  It can be prefixed with 'Bearer' or not. A bearer token is usually valid for a
  limited time and should be refreshed periodically.

```py
spark = Spark.Client(token='Bearer my-access-token') # with prefix
# or
spark = Spark.Client(token='my-access-token') # without prefix
```

- `oauth` (default: `os.getenv['CSPARK_CLIENT_ID']` and `os.getenv['CSPARK_CLIENT_SECRET']` or
  `os.getenv['CSPARK_OAUTH_PATH']`) indicates the OAuth2.0 client credentials.
  You can either provide the client ID and secret directly or the file path to
  the JSON file containing the credentials.

```py
spark = Spark.Client(oauth={'client_id': 'my-client-id', 'client_secret': 'my-client-secret'})
# or
spark = Spark.Client(oauth='path/to/oauth/credentials.json')
```

### Additional Settings

- `timeout` (default: `60000` ms) indicates the maximum amount of time that the
  client should wait for a response from Spark servers before timing out a request.

- `max_retries` (default: `2`) indicates the maximum number of times that the client
  will retry a request in case of a temporary failure, such as an unauthorized
  response or a status code greater than 400.

- `retry_interval` (default: `1` second) indicates the delay between each retry.

- `logger` (default: `True`) enables or disables the logger for the SDK.
  - If `bool`, determines whether or not the SDK should print logs.
  - If `dict`, the SDK will print logs in accordance with the specified keyword arguments.
  - If `LoggerOptions`, the SDK will print messages based on the specified options:
    - `context` (default: `CSPARK v{version}`): defines the context of the logs (e.g., `CSPARK v0.1.6`);
    - `disabled` (default: `False`) determines whether the logger should be disabled.
    - `colorful` (default: `True`) determines whether the logs should be colorful;
    - `timestamp` (default: `True`) determines whether the logs should include timestamps;
    - `datefmt` (default: `'%m/%d/%Y, %I:%M:%S %p'`) defines the date format for the logs;
    - `level` (default: `DEBUG`) defines the [logging level][logging-level] for the logs.

```py
spark = Spark.Client(logger=False)
# or
spark = Spark.Client(logger={'colorful': False})
```

## Client Errors

`SparkError` is the base class for all custom errors thrown by the SDK. There are
two types of it:

- `SparkSdkError`: usually thrown when an argument (user entry) fails to comply
  with the expected format. Because it's a client-side error, it will include the invalid
  entry as the `cause` in most cases.
- `SparkApiError`: when attempting to communicate with the API, the SDK will wrap
  any sort of failure (any error during the roundtrip) into `SparkApiError`, which
  includes the HTTP `status` code of the response and the `request_id`, a unique
  identifier of the request.

Some of the derived `SparkApiError` are:

| Type                      | Status | When                           |
| ------------------------- | ------ | ------------------------------ |
| `BadRequestError`         | 400    | invalid request                |
| `UnauthorizedError`       | 401    | missing or invalid credentials |
| `ForbiddenError`          | 403    | insufficient permissions       |
| `NotFoundError`           | 404    | resource not found             |
| `ConflictError`           | 409    | resource already exists        |
| `RateLimitError`          | 429    | too many requests              |
| `InternalServerError`     | 500    | server-side error              |
| `ServiceUnavailableError` | 503    | server is down                 |
| `UnknownApiError`         | `None` | unknown error                  |

## API Parity

The SDK aims to provide full parity with the Spark APIs over time. Below is a list
of the currently supported APIs.

[Authentication API](./docs/authentication.md) - manages access tokens using
OAuth2.0 Client Credentials flow:

- `Authorization.oauth.retrieve_token(config)` generates new access tokens.

[Services API](./docs/services.md) - manages Spark services:

- `Spark.services.create(data)` creates a new Spark service.
- `Spark.services.execute(uri, inputs)` executes a Spark service.
- `Spark.services.transform(uri, inputs)` executes a Spark service using `Transforms`.
- `Spark.services.get_versions(uri)` lists all the versions of a service.
- `Spark.services.get_schema(uri)` gets the schema of a service.
- `Spark.services.get_metadata(uri)` gets the metadata of a service.
- `Spark.services.download(uri)` downloads the excel file of a service.
- `Spark.services.recompile(uri)` recompiles a service using specific compiler versions.
- `Spark.services.validate(uri, data)` validates input data using static or dynamic validations.
- `Spark.services.delete(uri)` deletes an existing service, including all its versions.

[Batches API](./docs/batches.md) - manages asynchronous batch processing:

- `Spark.batches.describe()` describes the batch pipelines across a tenant.
- `Spark.batches.create(params, [options])` creates a new batch pipeline.
- `Spark.batches.of(id)` defines a client-side batch pipeline by ID.
- `Spark.batches.of(id).get_info()` gets the details of a batch pipeline.
- `Spark.batches.of(id).get_status()` gets the status of a batch pipeline.
- `Spark.batches.of(id).push(data, [options])` adds input data to a batch pipeline.
- `Spark.batches.of(id).pull([options])` retrieves the output data from a batch pipeline.
- `Spark.batches.of(id).dispose()` closes a batch pipeline.
- `Spark.batches.of(id).cancel()` cancels a batch pipeline.

[Log History API](./docs/history.md) - manages service execution logs:

- `Spark.logs.rehydrate(uri, call_id)` rehydrates the executed model into the original Excel file.
- `Spark.logs.download(data)` downloads service execution logs as `csv` or `json` file.

[ImpEx API](./docs/impex.md) - imports and exports Spark services:

- `Spark.impex.export(data)` exports Spark entities (versions, services, or folders).
- `Spark.impex.import_(data)` imports previously exported Spark entities into the platform.

[Other APIs](./docs/misc.md) - for other functionalities:

- `Spark.wasm.download(uri)` downloads a service's WebAssembly module.
- `Spark.files.download(url)` downloads temporary files issued by the Spark platform.

## Contributing

Feeling motivated enough to contribute? Great! Your help is always appreciated.

Please read [CONTRIBUTING.md][contributing-url] for details on the code of
conduct, and the process for submitting pull requests.

## Copyright and License

[Apache-2.0][license-url]

<!-- References -->
[version-img]: https://badge.fury.io/py/cspark.svg
[version-url]: https://pypi.python.org/pypi/cspark
[api-key-docs]: https://docs.coherent.global/spark-apis/authorization-api-keys
[bearer-token-docs]: https://docs.coherent.global/spark-apis/authorization-bearer-token
[oauth2-docs]: https://docs.coherent.global/spark-apis/authorization-client-credentials
[contributing-url]: https://github.com/Coherent-Partners/spark-python-sdk/blob/main/CONTRIBUTING.md
[license-url]: https://github.com/Coherent-Partners/spark-python-sdk/blob/main/LICENSE
[examples]: https://github.com/Coherent-Partners/spark-python-sdk/tree/main/examples
[documentation]: https://github.com/Coherent-Partners/spark-python-sdk/tree/main/docs
[logging-level]: https://docs.python.org/3/library/logging.html#logging-levels
