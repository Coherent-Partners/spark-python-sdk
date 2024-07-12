<!-- markdownlint-disable-file MD024 -->

# Services API

| Verb                                   | Description                                                              |
| -------------------------------------- | ------------------------------------------------------------------------ |
| `Spark.services.execute(uri, inputs)`  | [Execute a Spark service](#execute-a-spark-service).                     |
| `Spark.services.get_versions(uri)`     | [Get all the versions of a service](#get-all-the-versions-of-a-service). |
| `Spark.services.get_schema(uri)`       | [Get the schema for a given service](#get-the-schema-for-a-service).     |
| `Spark.services.get_metadata(uri)`     | [Get the metadata of a service](#get-the-metadata-of-a-service).         |

## Execute a Spark service

This method executes a Spark service with the input data and returns the output data.
It's the most common method for interacting with Spark services.

Currently, Spark supports two versions of the API: v3 and v4. The SDK will use
the [v3 format][v3-format] for a single input and the [v4 format][v4-format]
for multiple inputs.

By default, the SDK uses the v4 format for the output data. You may specify the
desired response format to retrieve the original format emitted by the API.

Check out the [API reference](https://docs.coherent.global/spark-apis/execute-api)
to learn more about Services API.

### Arguments

The method accepts a string or a `UriParams` object and optional keyword arguments,
which include the input data and metadata. See the use cases below.

- **Default inputs**:
  the following example demonstrates how to execute a service with default values.
  Obviously, the SDK ignores those default values. Under the hood, the SDK
  uses an empty object `{}` as the input data, which is an indicator for Spark to
  use the default inputs defined in the Excel file.

```py
spark.services.execute('my-folder/my-service')
# or
spark.services.execute(UriParams(folder='my-folder', service='my-service'))
```

- **Inputs only**:
  the above example is the simplest form of executing a service. In most cases, you
  will need to provide input data to the service. You can do so by passing an `inputs`
  object as the second argument.

```py
spark.services.execute('my-folder/my-service', inputs={'my_input': 42})
```

- **Inputs with metadata**: you can also provide metadata along with the input data.

```py
spark.services.execute(
    'my-folder/my-service',
    inputs={'my_input': 13},
    subservices=['sub1', 'sub2'],
    call_purpose='Demo',
)
```

- **String data**:
  you may use JSON string data as shown in the [API Tester](https://docs.coherent.global/navigation/api-tester).
  Basically, you are free to work with string data as long as it's a valid JSON
  string and follows the API v3 format.

```py
spark.services.execute('my-folder/my-service', inputs='{"my_input": 13}')
```

The previous examples will execute the latest version of a service using this
`folder/service[?version]` URI format. If you intend to execute a specific version,
you can do the following:

- using **version_id** (the fastest):
  `version_id` is the UUID of a particular version of the service.

```py
from cspark.sdk import UriParams

spark.services.execute('version/uuid')
# or
spark.services.execute(UriParams(version_id='uuid'))
```

- using **service_id**:
  `service_id` is the UUID of the service. It will execute the latest version of the service.

```py
from cspark.sdk import UriParams

spark.services.execute('service/uuid')
# or
spark.services.execute(UriParams(service_id='uuid'))
```

- using semantic **version**:
  `version` also known as revision number is the semantic version of the service.
  Keep in mind that using only `version` is not enough to locate a service. You must
  provide the `folder` and `service` names or the `service_id`.

```py
from cspark.sdk import UriParams

spark.services.execute('my-folder/my-service[0.1.0]')
# or
spark.services.execute(UriParams(folder='my-folder', service='service', version='0.1.0'))
```

- using **proxy** endpoints:
  `proxy` is the custom endpoint associated with the service.

```ts
spark.services.execute('proxy/custom-endpoint')
# or
spark.services.execute(UriParams(proxy='custom-endpoint'))
```

As you can tell, there are multiple flavors when it comes to locating a Spark
service and executing it. You can choose the one that suits best your needs. Here's
a summary of the parameters you can use for this method:

For the first argument, the service URI locator as a `string` or `UriParams` object:

| Property     | Type           | Description                                      |
| -----------  | -------------- | ------------------------------------------------ |
| _folder_     | `None \| str`  | The folder name.                                 |
| _service_    | `None \| str`  | The service name.                                |
| _version_    | `None \| str`  | The user-friendly semantic version of a service. |
| _version\_id_| `None \| str`  | The UUID of a particular version of the service. |
| _service\_id_| `None \| str`  | The service UUID (points to the latest version). |
| _proxy_      | `None \| str`  | The custom endpoint associated with the service. |
| _public_     | `None \| bool` | Whether to use the public endpoint.              |

For the other keyword arguments:

| Property             | Type          | Description                                      |
| -------------------- | ------------- | ------------------------------------------------ |
| _inputs_             | `None \| str \| Dict \| List` | The input data (single or many). |
| _response\_format_   | `raw \| typed \| alike` | Response data format to use (defaults to `alike`).|
| _active\_since_      | `None \| str` | The transaction date (helps pinpoint a version). |
| _source\_system_     | `None \| str` | The source system (defaults to `Spark Python SDK`).|
| _correlation\_id_    | `None \| str` | The correlation ID.                              |
| _call\_purpose_      | `None \| str` | The call purpose.                                |
| _tables\_as\_array_  | `None \| str \| List[str]`| Filter which table to output as JSON array.|
| _compiler\_type_     | `None \| str` | The compiler type (defaults to `Neuron`).        |
| _debug\_solve_       | `None \| bool`| Enable debugging for solve functions.            |
| _selected\_outputs_  | `None \| str \| List[str]`| Select which output to return.       |
| _outputs\_filter_    | `None \| str` | Use to perform advanced filtering of outputs .   |
| _echo\_inputs_       | `None \| bool`| Whether to echo the input data (alongside the outputs). |
| _subservices_        | `None \| str \| List[str]`| The list of sub-services to output.    |
| _downloadable_       | `None \| bool`| Produce a downloadable rehydrated Excel file for the inputs. |

### Returns

This method returns the output data of the service execution in the following
format:

- `original`: the output data as dictionary in its original format (as returned by the API).
- `alike`: the output data as dictionary in the v4 format whether it's a single or multiple inputs.

For instance, the output data of a service execution for a single input looks like this
when the `response_format` is set to `alike`:

```json
{
  "outputs": [{"my_output": 42}],
  "process_time": [2],
  "warnings": [null],
  "errors": [null],
  "service_chain": [null],
  "service_id": "uuid",
  "version_id": "uuid",
  "version": "1.2.3",
  "call_id": "uuid",
  "compiler_version": "1.2.0",
  "correlation_id": null,
  "request_timestamp": "1970-01-23T00:58:20.752Z"
}
```

You may wonder why the output data is wrapped in an array for a single input.
This is because the `alike` format is designed to work with both single and multiple
inputs. This should help maintain consistency in the output data format. But if you
prefer the original format emitted by the API, you can set the `response_format`
to `original`.

> [!IMPORTANT]
> Executing multiple inputs is a synchronous operation and may take some time to complete.
> The default timeout for this client is 60 seconds, and for Spark servers, it is 55 seconds.
> Another good practice is to split the batch into smaller chunks and submit separate requests.

## Get all the versions of a service

This method returns all the versions of a service.

### Arguments

The method accepts a string or keyword arguments `folder` and `service`.

```py
spark.services.get_versions('my-folder/my-service')
# or
spark.services.get_versions(folder='my-folder', service='my-service')
```

### Returns

```json
[
  {
    "id": "uuid",
    "createdAt": "1970-12-03T04:56:78.186Z",
    "engine": "my-service",
    "revision": "0.2.0",
    "effectiveStartDate": "1970-12-03T04:56:78.186Z",
    "effectiveEndDate": "1990-12-03T04:56:78.186Z",
    "isActive": true,
    "releaseNote": "some release note",
    "childEngines": null,
    "versionLabel": "",
    "defaultEngineType": "Neuron",
    "tags": null,
    "product": "my-folder",
    "author": "john.doe@coherent.global",
    "originalFileName": "my-service-v2.xlsx"
  },
  {
    "id": "86451865-dc5e-4c7c-a7f6-c35435f57dd1",
    "createdAt": "1970-12-03T04:56:78.186Z",
    "engine": "my-service",
    "revision": "0.1.0",
    "effectiveStartDate": "1970-12-03T04:56:78.186Z",
    "effectiveEndDate": "1980-12-03T04:56:78.186Z",
    "isActive": false,
    "releaseNote": null,
    "childEngines": null,
    "versionLabel": "",
    "defaultEngineType": "XConnector",
    "tags": null,
    "product": "my-folder",
    "author": "jane.doe@coherent.global",
    "originalFileName": "my-service.xlsx"
  }
]
```

## Get the schema for a service

This method returns the schema of a service. A service schema is a JSON object
that describes the structure of a service's input and output data. It includes
but not limited to the following information:

- Book summary
- Book properties
- Engine ID and inputs
- Service outputs
- Metadata

### Arguments

The method accepts a string or keyword arguments `folder` and `service`.

```py
spark.services.get_schema('my-folder/my-service')
# or
spark.services.get_schema(folder='my-folder', service='my-service')
```

### Returns

See a [sample service schema](./samples/service-swagger.json) for more information.

## Get the metadata of a service

This method returns the metadata of a service.

### Arguments

The method accepts a string or keyword arguments `folder` and `service`.

```py
spark.services.get_metadata('my-folder/my-service')
# or
spark.services.get_metadata(folder='my-folder', service='my-service')
```

### Returns

This method returns the output data of the service execution in the same format
as the [execute method](#execute-a-spark-service).

```json
{
  "outputs": [
    {
      "Metadata.Date": "1970-01-23",
      "Metadata.Number": 456,
      "Metadata.Text": "DEF",
      "METADATA.IMAGE": "data:image/png;base64,..."
    }
  ],
  "warnings": [null],
  "errors": [null],
  "service_id": "uuid",
  "version_id": "uuid",
  "version": "1.2.3",
  "process_time": 0,
  "call_id": "uuid",
  "compiler_type": "Type3",
  "compiler_version": "1.2.0",
  "source_hash": null,
  "engine_id": "hash-info",
  "correlation_id": null,
  "system": "SPARK",
  "request_timestamp": "1970-01-23T00:58:20.752Z"
}
```

[Back to top](#services-api) or [Next: Batches API](./batches.md)

<!-- References -->
[v3-format]: https://docs.coherent.global/spark-apis/execute-api/execute-api-v3
[v4-format]: https://docs.coherent.global/spark-apis/execute-api/execute-api-v4
