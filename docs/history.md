<!-- markdownlint-disable-file MD024 -->

# Log History API

| Verb                                  | Description                                                                                 |
| ------------------------------------- | ------------------------------------------------------------------------------------------- |
| `Spark.logs.rehydrate(uri, call_id)`  | [Rehydrate the executed model into the original excel file](#rehydrate-the-executed-model). |

> [!WARNING]
> The service execution history is a good source of truth for auditing and debugging
> purposes. Though practical, log history is not intended to be a data storage solution.
> So, do use the following methods **responsibly**.

## Rehydrate the executed model

This method allows you to "rehydrate" the executed model into the original excel file
and download it to your local machine.

> Rehydration is the process of regenerating the model with the input data used
> during the execution.

### Arguments

You may indicate the service URI as a string or a `UriParams` object or optional keyword
arguments. Additionally, other keyword arguments such the call ID is required to
rehydrate the model.

```python
spark.logs.rehydrate('my-folder/my-service', call_id='call-id')
```

Here's a list of keyword parameters you can use:

| Property    | Type          | Description                           |
| ----------- | ------------- | ------------------------------------- |
| _call\_id_  | `str`         | The call ID of the service execution. |
| _folder_    | `str \| None` | The folder name.                      |
| _service_   | `str \| None` | The service name.                     |
| _index_     | `int \| None` | For [v4 format][v4-format], indicate which record of the list to rehydrate (e.g., `0` is the first record). |

```python
spark.logs.rehydrate('my-folder/my-service', call_id='call-id') # for v3 format
# or
spark.logs.rehydrate('my-folder/my-service', call_id='call-id', index=0) # for v4 format
```

Do note that the `index` parameter is only valid for the synchronous batch execution (aka v4 format).
If you're rehydrating an API call log that used v4 format and you do not specify the `index` parameter,
the Spark platform will default to the last record. And if the `index` is out of bounds, the platform will
throw a bad request error.

> [!TIP]
> Another way of achieving the same result is by setting the `downloadable` metadata
> field as `True` at the time of executing the service. See the
> [Spark.services.execute()](./services.md#execute-a-spark-service) method for more information.

### Returns

when successful, this method returns:

- a buffer containing the file content (excel file);
- a JSON payload including essential information such as the download URL.

**JSON payload example:**

```json
{
  "status": "Success",
  "response_data": {
    "download_url": "https://entitystore.my-env.coherent.global/docstore/api/v1/documents/versions/tokens/some-token/file.xlsx"
  },
  "response_meta": {
    "service_id": "uuid",
    "version_id": "uuid",
    "version": "1.2.3",
    "process_time": 0,
    "call_id": "uuid",
    "compiler_type": "Neuron",
    "compiler_version": null,
    "source_hash": null,
    "engine_id": "alpha-numeric-id",
    "correlation_id": null,
    "parameterset_version_id": null,
    "system": "SPARK",
    "request_timestamp": "1970-12-03T04:56:56.186Z"
  },
  "error": null
}
```

Here's a full example how to harness this method:

```python
import cspark.sdk as Spark

spark = Spark.Client(env='my-env', tenant='my-tenant', token='bearer token')
with spark.logs as logs:
    response = logs.rehydrate('my-folder/my-service', call_id='uuid')
    with open('path/to/my-rehydrated-excel.xlsx', 'wb') as file:
        file.write(response.buffer) # write downloaded file to disk
        print('file rehydrated successfully 🎉')
        print(response.data) # print download info
```

[Back to top](#log-history-api) or [Next: ImpEx API](./impex.md)

<!-- References -->

[v4-format]: https://docs.coherent.global/spark-apis/execute-api/execute-api-v4
