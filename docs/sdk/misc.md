<!-- markdownlint-disable-file MD024 -->

# Other APIs

| Verb                        | Description                                                                         |
| --------------------------- | ----------------------------------------------------------------------------------- |
| `Spark.health.check()`      | [Check the health status of a Spark environment](#check-the-health-status-of-a-spark-environment). |
| `Spark.config.get()`        | [Fetch the platform configuration](#fetch-the-platform-configuration). |
| `Spark.wasm.download(uri)`  | [Download a service's WebAssembly module](#download-a-services-webassembly-module). |
| `Spark.files.download(url)` | [Download a Spark file](#download-a-spark-file).                                    |

## Check the health status of a Spark environment

This method checks the health status of a Spark environment as described in the
[API reference](https://docs.coherent.global/integrations/diagnose-spark-connectivity).

### Arguments

This method does not require any arguments as it relies on the current `Spark.Config` (i.e., `env`,
`tenant`, or `base_url`) to determine which Spark environment to check.

```python
import cspark.sdk as Spark

Spark.Client(env='my-env', tenant='my-tenant', token='open').health.check()
```

> [!NOTE]
> Actually, no authentication is required to check the health status of a Spark environment.
> A convenient way to do this without the need for a client instance is to use the
> `Spark.Client.health_check(url)` static method, where `url` can either be the base
> URL or the environment name.

```python
import cspark.sdk as Spark

Spark.Client.health_check('my-env')
```

### Returns

When successful, this method returns a dictionary containing the health status of the
Spark environment.

```json
{"status": "UP" }
```

> [!TIP]
> You can simply use the `Spark.health.ok()` method to check if the Spark environment
> is healthy. This method returns a boolean value indicating whether the environment
> is up and running or not.

## Fetch the platform configuration

The platform or Spark configuration refers to the SaaS configuration for the current
tenant (and user), which includes information such as batch size, timeout, supporter
compilers, etc.

### Arguments

This method does not require any arguments and will fetch the SaaS configuration
via API, which should not be confused with the SDK configuration.

```python
from cspark.sdk import Config

base_url = 'https://spark.my-env.coherent.global/my-tenant'
token = 'my-access-token' # only this security scheme is supported for this API
Config(base_url=base_url, token=token).get()
```

### Returns

This method returns a dictionary containing the platform configuration.
See the [sample configuration](../../docs/samples/spark-config.json) for more information.

## Download a service's WebAssembly module

This method helps you download a service's [WebAssembly](https://webassembly.org/)
module.

[WebAssembly](https://webassembly.org/) (WASM) is a low-level binary format for
executing code in a stack-based virtual machine. It serves as a compilation target
for high-level programming languages, enabling efficient execution across web platforms.

In Spark's context, a WebAssembly module is a self-contained package that bundles
the compiled service logic with its supporting files. This modular approach ensures
consistent execution in both web browsers and Node.js environments, making Spark
services highly portable and performant.

Check out the [API reference](https://docs.coherent.global/spark-apis/webassembly-module-api)
for more information.

### Arguments

You may pass in the service URI as `string` in the following format:

- `version/{version_id}` - **preferred**
- `service/{service_id}`
- `{folder}/{service}`

```python
spark.wasm.download('version/uuid')
```

Alternatively, you can pass in the following parameters as keyword arguments.

| Property      | Type          | Description                      |
| ------------- | ------------- | -------------------------------- |
| _folder_      | `str \| None` | The folder name.                 |
| _service_     | `str \| None` | The service name.                |
| _version\_id_ | `str \| None` | The version UUID of the service. |
| _service\_id_ | `str \| None` | The service UUID (points to the latest version).|

```python
spark.wasm.download(version_id='uuid')
```

### Returns

When successful, this method returns a buffer containing the WebAssembly module.
Here's a full example of how to download a service's WebAssembly module and save
it to disk:

```python
import cspark.sdk as Spark

spark = Spark.Client(env='my-env', tenant='my-tenant', token='bearer token')
with spark.wasm as wasm:
    response = wasm.download(version_id='uuid')
    with open('wasm.zip', 'wb') as file:
        file.write(response.buffer) # write downloaded file to disk
        print('file downloaded successfully 🎉')
```

The downloaded zip file should have the following files:

- `my-service.wasm`: the WebAssembly module with the service's logic
- `my-service.js`: the JavaScript glue code to interact with the WebAssembly module
- `my-service.data`: the service's static data (binary file)
- `my-serviceDefaultValidations.json`: the default or static validation schema
- `checksums.md5`: the checksums of the files in the zip (.data, .wasm, .js)
- `my-service_Jsonformspec.json` (optional): the service execution's JSON form specification
  (useful for generating UI elements such as input, select, etc.)

## Download a Spark file

Some Spark APIs may generate temporary files upon execution. This method helps you
download these files, which oftentimes require a valid token for access.

### Arguments

This method requires a valid URL as a `string`.

```python
spark.files.download('https://my-spark-file-url')
```

Some of the generated files carry a token for access in the URL. In such cases, you
can use a static method to download the file since it doesn't require any Spark settings.

```python
import cspark.sdk as Spark

Spark.Client.download('https://my-spark-file-url/with/token')
```

It should be noted that the `Client.download()` method is a static one and doesn't require
any Spark configuration. It also accepts a second argument, [Authorization](../../src/cspark/sdk/_auth.py),
which can be used if user authorization is required to access and download a file.

```py
from cspark.sdk import Client, Authorization

auth = Authorization(token='bearer token')
Client.download('https://my-spark-file-url', auth)
```

### Returns

When successful, this method returns a buffer containing the file. You may then write
this buffer to disk (as shown above) or process it further.

[Back to top](#other-apis) or [Main Documentation](../readme.md)
