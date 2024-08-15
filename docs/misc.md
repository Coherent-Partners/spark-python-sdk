<!-- markdownlint-disable-file MD024 -->

# Other APIs

| Verb                        | Description                                                                         |
| --------------------------- | ----------------------------------------------------------------------------------- |
| `Spark.wasm.download(uri)`  | [Download a service's WebAssembly module](#download-a-services-webassembly-module). |
| `Spark.files.download(url)` | [Download a Spark file](#download-a-spark-file).                                    |

## Download a service's WebAssembly module

This method helps you download a service's [WebAssembly](https://webassembly.org/)
module.

Roughly speaking, WebAssembly (or WASM) is a binary instruction format
for a stack-based virtual machine. It's designed as a portable compilation target
for programming languages, enabling deployment on the web for client and server
applications.

In the context of Spark, a WebAssembly module refers to a cohesive bundle of
files designed for portability and execution across web and Node.js environments.
This bundle typically includes the WebAssembly representation of the Spark service's
encapsulated logic along with associated JavaScript files. By packaging these
components together, a Spark WASM module becomes executable within both browser and
Node environments.

Check out the [API reference](https://docs.coherent.global/spark-apis/webassembly-module-api)
for more information.

### Arguments

You may pass in the service URI as `string` in the following format:

- `version/uuid` (e.g., `version/123e4567-e89b-12d3-a456-426614174000`) - **preferred**
- `service/uuid` (e.g., `service/123e4567-e89b-12d3-a456-426614174000`)
- `folder/service` (e.g., `my-folder/my-service`)

```python
spark.wasm.download('version/uuid')
```

Alternatively, you can pass in the following parameters as an `object`.

| Property      | Type     | Description                      |
| ------------- | -------- | -------------------------------- |
| _folder_      | `string` | The folder name.                 |
| _service_     | `string` | The service name.                |
| _version\_id_ | `string` | The version UUID of the service. |
| _service\_id_ | `string` | The service UUID.                |

> [!NOTE]
> As of now, only the `version_id` should be used to download the WebAssembly module.
> The other properties are currently being tested. Otherwise, they might throw an `UnknownApiError`.

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
any Spark configuration. It also accepts a second argument, [Authorization](../src/cspark/sdk/_auth.py),
which can be used if user authorization is required to access and download a file.

```py
from cspark.sdk import Client, Authorization

auth = Authorization(token='bearer token')
Client.download('https://my-spark-file-url', auth)
```

### Returns

When successful, this method returns a buffer containing the file. You may then write
this buffer to disk (as shown above) or process it further.

[Back to top](#other-apis) or [Main Documentation](./readme.md)
