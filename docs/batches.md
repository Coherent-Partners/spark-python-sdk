<!-- markdownlint-disable-file MD024 -->

# Batch API

| Verb                                        | Description                                                                        |
| -----------------------------------------   | ---------------------------------------------------------------------------------- |
| `Spark.batches.execute(uri, inputs)`        | [Execute multiple records synchronously](#execute-multiple-records-synchronously). |

## Execute multiple records synchronously

This method helps you execute multiple records synchronously. It's useful when you
have a batch of records to process and you want to execute them all at once. This
operation is similar to the `Spark.services.execute` method but with multiple records.

### Arguments

The method accepts a string or a `UriParams` object and a second object with the
input data as arguments.

```py
data = [{ value: 11 }, { value: 12 }, { value: 13 }]
spark.batches.execute('my-folder/my-service', inputs=data, call_purpose='Batch execution')
```

For the first argument, `UriParams` object:

| Property     | Type   | Description                          |
| -----------  | ------ | ------------------------------------ |
| _folder_     | `str`  | The folder name.                     |
| _service_    | `str`  | The service name.                    |
| _version\_id_| `str`  | The version UUID of the service.     |
| _service\_id_| `str`  | The service UUID.                    |
| _version_    | `str`  | The semantic version of the service. |
| _public_     | `bool` | Whether to use the public endpoint.  |

For the keyword arguments:

| Property          | Type    | Description                      |
| --------------    | ------- | -------------------------------- |
| _inputs_          | `Any[]` | The input data.                  |
| _raw_             | `str`   | The input data in its raw form.  |
| _version\_id_     | `str`   | The version ID of the service.   |
| _active\_since_   | `str`   | The transaction date.            |
| _source\_system_  | `str`   | The source system.               |
| _correlation\_id_ | `str`   | The correlation ID.              |
| _call\_purpose_   | `str`   | The call purpose.                |
| _subservices_     | `str \| str[]` | The comma-separated subservice names. |
| _output_          | `str \| str[]` | Expect specific requested output.     |

### Returns

This method returns the output data of the service execution in the following
format (aka v4 format).

```json
{
  "outputs": [{ "my_output": 40 }, { "my_output": 41 }, { "my_output": 42 }],
  "process_time": [1, 1, 1],
  "warnings": [null, null, null],
  "errors": [null, null, null],
  "service_id": "uuid",
  "version_id": "uuid",
  "version": "0.4.2",
  "call_id": "uuid",
  "compiler_version": "1.12.0",
  "correlation_id": null,
  "request_timestamp": "1970-12-03T04:56:78.186Z"
}
```

> [!IMPORTANT]
> This operation is synchronous and may take some time to complete. The default
> timeout is 60 seconds. If you have a large batch of records, you may want to
> increase the timeout to avoid any issues. Another good practice is to split
> the batch into small chunks and submit separate requests.

Check out the [API reference](https://docs.coherent.global/spark-apis/execute-api/execute-api-v4#sample-request)
to learn more about the API v4 format of the inputs and outputs.
