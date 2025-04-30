<!-- markdownlint-disable-file MD024 -->

# Log History API

| Verb                                 | Description                                                                                 |
| ------------------------------------ | ------------------------------------------------------------------------------------------- |
| `Spark.logs.rehydrate(uri, call_id)` | [Rehydrate the executed model into the original excel file](#rehydrate-the-executed-model). |
| `Spark.logs.download(data)`          | [Download service execution logs as csv or json file](#download-service-execution-logs).    |

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
| _index_     | `int \| None` | For [v4 format][v4-format], indicate which record of the list to rehydrate (e.g., `0` is the 1st record). |
| _legacy_    | `bool`        | Use the legacy rehydration format (defaults to `False`).|

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

Here's a full example of how to harness this method:

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

## Download service execution logs

This method allows you to export service execution logs in either CSV or JSON
format to your local machine. It streamlines the download process by handling the
complete workflow: initiating the download job, monitoring its status, and retrieving
the final zip file once ready. If the download process encounters any issues or
fails to generate a downloadable file, the method raises a `SparkError`.

If you want to have more fine-grained control over the download process, you can use
respectively the `Spark.logs.downloads.initiate(uri, [type])` and
`Spark.logs.downloads.get_status(uri, [type])` methods to initiate a download
job and check its status until it's finished. Do note that the status check is
subject to `RetryTimeoutError` when it reaches the maximum number of retries.

### Arguments

This method accepts the following keyword arguments:

| Property          | Type                 | Description                                           |
| ----------------- | -------------------- | ----------------------------------------------------- |
| _folder_          | `str`                | The folder name.                                      |
| _service_         | `str`                | The service name.                                     |
| _version\_id_     | `None \| string`     | The particular service version for the download.      |
| _type_            | `csv \| json`        | The file type (defaults to `json`).                   |
| _call\_ids_       | `None \| List[str]`  | An array of call IDs to download logs for.            |
| _start\_date_     | `None \| str \| int \| datetime` | The start date (format: `YYYY-MM-DD[THH:MM:SS.SSSZ]`).|
| _end\_date_       | `None \| str \| int \| datetime` | The end date (format: `YYYY-MM-DD[THH:MM:SS.SSSZ]`). |
| _correration\_id_ | `string`             | The correlation ID (possible fallback for `call_ids`).|
| _source\_system_  | `string`             | The source system (possible fallback for `call_ids`). |
| _max\_retries_    | `None \| int`   | The number of retries to attempt (defaults to `Config.max_retries`).|
| _retry\_interval_ | `None \| float` | The interval between retries in seconds (defaults to `Config.retry_interval`).|

```python
spark.logs.download(
    folder='my-folder',
    service='my-service',
    call_ids=['uuid1', 'uuid2', 'uuid3'],
    type='json',
    max_retries=5,
    retry_interval=3,
)
```

### Returns

When successful, this method returns:

- a buffer containing the file content (zip file);
- a JSON payload including essential information such as the download URL.

**JSON payload example:**

```json
{
  "status": "Success",
  "response_data": {
    "download_url": "https://entitystore.my-env.coherent.global/docstore/api/v1/documents/versions/tokens/some-token/file.zip"
  },
  "response_meta": {
    // similar to the rehydrate method...
    "system": "SPARK",
    "request_timestamp": "1970-12-03T04:56:56.186Z"
  },
  "error": null
}
```

The downloaded zip file should contain the logs in the requested format. For example,
if you requested a JSON file, the logs should be similar to this:

```json
[
  {
    "EngineCallId": "uuid",
    "LogTime": "1970-12-03T04:56:56.186Z",
    "TransactionDate": "1970-12-03T04:56:56.186Z",
    "SourceSystem": "Spark Python SDK",
    "Purpose": "JSON Download",
    "UserName": "john.doe@coherent.global",
    "HostName": "excel.my-env.coherent.global",
    "Tenant": "my-tenant",
    "Service": "my-service",
    "Product": "my-folder",
    "EngineDetails": {
      "response_data": { "outputs": { "my_output": 42 }, "warnings": null, "errors": null, "service_chain": null },
      "response_meta": {
        "spark_total_time": 123,
        "service_id": "uuid",
        "version_id": "uuid",
        "version": "1.2.3",
        "process_time": 10,
        "call_id": "uuid",
        "compiler_type": "Neuron",
        "compiler_version": "1.12.0",
        "source_hash": null,
        "engine_id": "alpha-numeric-id",
        "correlation_id": "",
        "parameterset_version_id": null,
        "system": "SPARK",
        "request_timestamp": "1970-12-03T04:56:56.186Z"
      },
      "request_data": { "inputs": { "my_input": 13 } },
      "request_meta": {
        "service_uri": null,
        "service_id": "uuid",
        "version": "1.2.3",
        "version_id": "uuid",
        "transaction_date": "1970-12-03T04:56:56.186Z",
        "call_purpose": "JSON Download",
        "source_system": "Spark Python SDK",
        "correlation_id": "",
        "requested_output": null,
        "service_category": "",
        "compiler_type": "Neuron",
        "array_outputs": null,
        "response_data_inputs": false,
        "parameterset_version_id": null,
        "validation_type": null
      }
    }
  }
]
```

And its CSV equivalent should look like this:

```csv
Description,Log Time,Transaction date,Version,Version ID,User name,Source system,Correlation ID,Call purpose,Call ID,Calc time (ms),Total time (ms),my_input,my_output,Error Details,Warning Details
,1970-12-03T04:56:56+00:00,1970-12-03T04:56:56+00:00,1.2.3,uuid,john.doe@coherent.global,SPARK,,Spark Python SDK,uuid,10,561,13,42,,
```

Check out the [API reference](https://docs.coherent.global/spark-apis/api-call-history-apis/download-log-as-csv)
for more information.

[Back to top](#log-history-api) or [Next: ImpEx API](./impex.md)

<!-- References -->

[v4-format]: https://docs.coherent.global/spark-apis/execute-api/execute-api-v4
