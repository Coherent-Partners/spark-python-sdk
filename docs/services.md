<!-- markdownlint-disable-file MD024 -->

# Service API

| Verb                                        | Description                                                                        |
| -----------------------------------------   | ---------------------------------------------------------------------------------- |
| `Spark.services.execute(uri, inputs)`       | [Execute a Spark service](#execute-a-spark-service).                               |
| `Spark.services.validate(uri, inputs)`      | [Validate input data using static or dynamic validations](#validate-input-data).   |
| `Spark.services.get_versions(uri)`          | [Get all the versions of a service](#get-all-the-versions-of-a-service).           |
| `Spark.services.get_schema(uri)`            | [Get the schema for a given service](#get-the-schema-for-a-service).               |
| `Spark.services.get_metadata(uri)`          | [Get the metadata of a service](#get-the-metadata-of-a-service).                   |

## Execute a Spark service

This method executes a Spark service with the given input data. It uses the API v3
format to execute the service.

Check out the [API reference](https://docs.coherent.global/spark-apis/execute-api/execute-api-v3)
to learn more about the API v3 format of the inputs and outputs.

### Arguments

The method accepts a string or a `UriParams` object and optionally a second object
with the input data as arguments. See the use cases below.

- **Default inputs**:
  the following example demonstrates how to execute a service with default values.
  Obviously, the SDK ignores what those default values are. Under the hood, the SDK
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
spark.services.execute('my-folder/my-service', inputs={ 'my_input': 42 })
```

- **Inputs with metadata**: you can also provide metadata along with the input data.

```py
from cspark.sdk import ExecuteData

data = ExecuteData(inputs={'my_input': 13 }, subservices=['sum', 'product'], call_purpose='Demo')
spark.services.execute('my-folder/my-service', data=data)
```

- **Raw data**:
  you may use JSON string data as shown in the [API Tester](https://docs.coherent.global/navigation/api-tester).
  Basically, you are free to work with raw data as long as it's a valid JSON
  string and follows the API v3 format.

```py
raw = """{
  "request_data": { "inputs": { "my_input": 13 } },
  "request_meta": { "version_id": "uuid", "call_purpose": "Demo" }
}
"""

spark.services.execute('my-folder/my-service', raw=raw)
```

The previous examples will execute the latest version of a service. If you want
to execute a specific version, you can do the following:

- using **version_id** (the fastest):
  `version_id` is the UUID of a particular version of the service.

```py
from cspark.sdk import UriParams, ExecuteData

spark.services.execute('version/uuid')
# or
spark.services.execute(UriParams(version_id='uuid'))
# or
spark.services.execute('my-folder/my-service', data=ExecuteData(version_id='uuid'))
```

- using **service_id**:
  `service_id` is the UUID of the service. It will execute the latest version of the service.

```py
from cspark.sdk import UriParams, ExecuteData

spark.services.execute('service/uuid')
# or
spark.services.execute(UriParams(service_id='uuid'))
# or
spark.services.execute('my-folder/my-service', data=ExecuteData(service_id='uuid'))
```

- using semantic **version**:
  `version` also known as revision number is the semantic version of the service.

```py
from cspark.sdk import UriParams, ExecuteData

spark.services.execute('my-folder/my-service[0.1.0]')
# or
spark.services.execute(UriParams(version='0.1.0'))
# or
spark.services.execute('my-folder/my-service', data=ExecuteData(version='0.1.0'))
```

- using **proxy** endpoints:
  `proxy` is the custom endpoint associated with the service.

```ts
spark.services.execute('my-proxy/endpoint')
```

As you can tell, there are multiple flavors when it comes to locating a Spark
service and executing it. You can choose the one that suits best your needs. Here's
a summary of the parameters you can use for this method:

For the first argument, `UriParams` object:

| Property     | Type   | Description                                      |
| -----------  | ------ | ------------------------------------------------ |
| _folder_     | `str`  | The folder name.                                 |
| _service_    | `str`  | The service name.                                |
| _version\_id_ | `str`  | The UUID of a particular version of the service. |
| _service\_id_ | `str`  | The service UUID.                                |
| _version_    | `str`  | The semantic version of the service.             |
| _proxy_      | `str`  | The custom endpoint associated with the service. |
| _public_     | `bool` | Whether to use the public endpoint.              |

For the other keyword arguments:

| Property             | Type             | Description                                      |
| -------------------- | ---------------- | ------------------------------------------------ |
| _inputs_             | `Dict[str, Any]` | The input data.                                  |
| _raw_                | `str`            | The input data in its raw form.                  |
| _data_               | `ExecuteData`    | Executable input data with metadata.             |
| _data.inputs_        | `Dict[str, Any]` | Alternate way to pass in input data.             |
| _data.service\_uri_   | `str`            | The service URI.                                 |
| _data.version\_id_    | `str`            | The version ID of the service.                   |
| _data.service\_id_    | `str`            | The service UUID.                                |
| _data.version_       | `str`            | The semantic version.                            |
| _data.active\_since_  | `str`            | The transaction date.                            |
| _data.source\_system_ | `str`            | The source system.                               |
| _data.correlation\_id_| `str`            | The correlation ID.                              |
| _data.call\_purpose_  | `str`            | The call purpose.                                |
| _data.outputs_       | `str \| List[str]`| The array of output names.                      |
| _data.compiler\_type_ | `str`            | The compiler type (e.g., `Neuron`).              |
| _data.debug\_solve_   | `bool`           | Enable debugging for solve functions.            |
| _data.output_        | `str \| List[str]`| Expect specific requested output.               |
| _data.output\_regex_  | `str`            | Expect specific requested output using regex.    |
| _data.with\_inputs_   | `bool`           | Whether to include input data in the response.   |
| _data.subservices_   | `str \| List[str]`| The comma-separated subservice names if string. |
| _data.downloadable_  | `bool`           | Whether to include a download URL of the Excel in the response. |

### Returns

This method returns the output data of the service execution in the following
format (aka v3 format).

```json
{
  "status": "Success",
  "error": null,
  "response_data": {
    "outputs": { "my_output": 42 },
    "warnings": null,
    "errors": null,
    "service_chain": null
  },
  "response_meta": {
    "service_id": "uuid",
    "version_id": "uuid",
    "version": "1.2.3",
    "process_time": 0,
    "call_id": "uuid",
    "compiler_type": "Neuron",
    "compiler_version": "1.2.0",
    "source_hash": null,
    "engine_id": "hash-info",
    "correlation_id": null,
    "system": "SPARK",
    "request_timestamp": "1970-01-23T00:58:20.752Z"
  }
}
```

## Validate input data

This method validates the input data using static or dynamic validations set in
the Excel file. This is useful for building frontend applications that connect
to Spark services.

- `static` validation is a cell validation that's only affected by its own formula.
- `dynamic` validation is a cell validation that depends on other cells/inputs.

Check out the [API reference](https://docs.coherent.global/spark-apis/validation-api)
to learn more about validation of the inputs and outputs.

> **Note:** This method works similarly to the `Spark.services.execute` method but
> with a different purpose. If you want to know more about the input and output
> data format, check the [excute(...)](#execute-a-spark-service) method.

### Arguments

This method follows the same pattern as the `execute` method. To specify which type
of validation to use, you must provide the `validation_type` property as part of
the `ExecuteData` object.

```py
from cspark.sdk import ExecuteData

data = ExecuteData(inputs={'my_input': 13 }, validation_type='dynamic', call_purpose='Demo')
spark.services.validate('my-folder/my-service', data=data)
```

### Returns

```json
{
  "status": "Success",
  "error": null,
  "response_data": {
    "outputs": {
      "my_static_input": {
        "validation_allow": "List",
        "validation_type": "static",
        "dependent_inputs": ["my_dynamic_input"],
        "min": null,
        "max": null,
        "options": ["a", "b"],
        "ignore_blank": true
      },
      "my_dynamic_input": {
        "validation_allow": "List",
        "validation_type": "dynamic",
        "dependent_inputs": null,
        "min": null,
        "max": null,
        "options": ["x", "y", "z"],
        "ignore_blank": false
      }
    },
    "warnings": null,
    "errors": null,
    "service_chain": null
  },
  "response_meta": {
    "service_id": "uuid",
    "version_id": "uudi",
    "version": "0.4.2",
    "process_time": 0,
    "call_id": "uuid",
    "compiler_type": "Type3",
    "compiler_version": "1.12.0",
    "source_hash": null,
    "engine_id": "alpha-numeric-id",
    "correlation_id": null,
    "parameterset_version_id": null,
    "system": "SPARK",
    "request_timestamp": "1970-01-23T00:58:20.752Z"
  }
}
```

See more examples of [static validation](https://docs.coherent.global/spark-apis/validation-api#validation_type-static)
and [dynamic validation](https://docs.coherent.global/spark-apis/validation-api#validation_type-dynamic-part-1).

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
{
  "status": "Success",
  "message": null,
  "errorCode": null,
  "data": [
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
}
```

## Get the schema for a service

This method returns the schema of a service. A service schema is a JSON object
that describes the structure of the input and output data of a service. It includes
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

```json
{
  "status": "Success",
  "error": null,
  "response_data": {
    "outputs": {
      "Metadata.Date": "1970-01-23",
      "Metadata.Number": 456,
      "Metadata.Text": "DEF",
      "METADATA.IMAGE": "data:image/png;base64,..."
    },
    "warnings": null,
    "errors": null,
    "service_chain": null
  },
  "response_meta": {
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
}
```
