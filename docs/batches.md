<!-- markdownlint-disable-file MD024 -->

# Batches API

| Verb                                        | Description                            |
| ------------------------------------------- | -------------------------------------- |
| `Spark.batches.describe()`                  | [Describe batch pipelines across a tenant](#describe-batch-pipelines-across-a-tenant).|
| `Spark.batches.create(params, [options])`   | [Create a new batch pipeline](#create-a-new-batch-pipeline). |
| `Spark.batches.of(id)`                      | [Define a client-side batch pipeline by ID](#define-a-client-side-batch-pipeline-by-id).|
| `Spark.batches.of(id).get_info()`           | [Get the details of a batch pipeline](#get-the-details-of-a-batch-pipeline). |
| `Spark.batches.of(id).get_status()`         | [Get the status of a batch pipeline](#get-the-status-of-a-batch-pipeline).  |
| `Spark.batches.of(id).push(data, [options])`| [Add input data to a batch pipeline](#add-input-data-to-a-batch-pipeline).  |
| `Spark.batches.of(id).pull([options])`      | [Retrieve the output data from a batch pipeline](#retrieve-the-output-data-from-a-batch-pipeline).|
| `Spark.batches.of(id).dispose()`            | [Close a batch pipeline](#close-a-batch-pipeline).|
| `Spark.batches.of(id).cancel()`             | [Cancel a batch pipeline](#cancel-a-batch-pipeline).|

The [Batches API][batch-apis] (in Beta) offers a set of endpoints that facilitate
executing a Spark service for a large volume of input data. Spark provides a dedicated
infrastructure specifically designed for parallel processing, capable of scaling up
or down based on the data volume that needs to be processed.

Utilizing this API will ensure optimal performance and scalability for your data
processing tasks.

> [!NOTE]
> It is important to note that the Batches API is recommended when dealing with
> datasets consisting of more than 10,000, with a calculation time of about 500ms or more.
> Unless you have specific requirements or reasons to use a different approach,
> such as [Services API](./services.md) as an alternative, this API is the way to go.

For more information on the Batches API and its endpoints, refer to the [API reference][batch-apis].

## Describe batch pipelines across a tenant

This method returns a list of all the batch pipelines available across a tenant.
It helps you keep track of your batch pipelines and their statuses. Remember that
this will only provide information about batches that are in progress or recently
completed (i.e., within the past hour).

```py
spark.batches.describe()
```

### Arguments

This method does not require any arguments.

### Returns

The method returns a list of batch pipelines along with their details. You will only
retrieve information about batches initiated by your user account unless you have
been granted access (e.g., `supervisor:pf`) to view other users' batches.

```json
{
  "in_progress_batches": [],
  "recent_batches": [
    {
      "object": "batch",
      "id": "uuid",
      "data": {
        "pipeline_status": "closed",
        "summary": {
          "records_submitted": 123,
          "records_failed": 0,
          "records_completed": 123,
          "compute_time_ms": 13,
          "batch_time_ms": 456
        },
        "response_timestamp": "1970-12-03T04:56:12.186Z",
        "batch_status": "completed",
        "created_by": "john.doe@coherent.global",
        "created_timestamp": "1970-12-03T04:56:12.186Z",
        "updated_timestamp": "1970-12-03T04:57:12.186Z",
        "service_uri": "my-folder/my-service[0.4.2]"
      }
    }
  ],
  "tenant": {
    "configuration": {
      "input_buffer_allocated_bytes": 0,
      "output_buffer_allocated_bytes": 0,
      "max_workers": 100
    },
    "status": {
      "input_buffer_used_bytes": 0,
      "input_buffer_remaining_bytes": 0,
      "output_buffer_used_bytes": 0,
      "output_buffer_remaining_bytes": 0,
      "workers_in_use": 0
    }
  },
  "environment": { "update": 123 }
}
```

## Create a new batch pipeline

This method allows you to start a new batch pipeline, which is a necessary step
before you can perform any operations on it.

> [!IMPORTANT]
> It is a good practice to retain the `id` of the newly-created batch pipeline.
> This identifier will be used to reference the batch pipeline in subsequent operations.

### Arguments

The method accepts a string or a `UriParams` object and optional keyword arguments,
which include metadata and other pipeline configuration settings (experimental).

For the first argument, the service URI locator as a string or `UriParams` object:

| Property     | Type           | Description                                      |
| -----------  | -------------- | ------------------------------------------------ |
| _folder_     | `None \| str`  | The folder name.                                 |
| _service_    | `None \| str`  | The service name.                                |
| _version_    | `None \| str`  | The user-friendly semantic version of a service. |
| _version\_id_| `None \| str`  | The UUID of a particular version of the service. |
| _service\_id_| `None \| str`  | The service UUID (points to the latest version). |

```py
spark.batches.create('my-folder/my-service')
# or
spark.batches.create(UriParams(folder='my-folder', service='my-service'))
```

If needed, you can also provide additional keyword arguments to configure how the
batch pipeline, once created, will perform its operations.

| Property             | Type          | Description                                      |
| -------------------- | ------------- | ------------------------------------------------ |
| _active\_since_      | `None \| str` | The transaction date (helps pinpoint a version). |
| _source\_system_     | `None \| str` | The source system (defaults to `Spark Python SDK`).|
| _correlation\_id_    | `None \| str` | The correlation ID.                              |
| _call\_purpose_      | `None \| str` | The call purpose.                                |
| _subservices_        | `None \| str \| List[str]`| The list of subservice to output.    |
| _selected\_outputs_  | `None \| str \| List[str]`| Select which output to return.       |
| _unique\_record\_key_| `None \| str \| List[str]`| Indicate certain inputs as unique identifiers. |

The following optional arguments are experimental and may change in future releases.

| Property            | Type            | Description                                      |
| ------------------- | --------------- | ------------------------------------------------ |
| _min\_runners_      | `None \| int`   | Number of concurrent runners used to start a batch in a VM before ramping up (defaults to 10). |
| _max\_runners_      | `None \| int`   | Maximum number of concurrent runners allowed in a VM (defaults to 100). |
| _chunks\_per\_vm_   | `None \| int`   | Number of chunks to be processed by all VMs (defaults to 2). |
| _runners\_per\_vm_  | `None \| int`   | Number of runners per VM (defaults to 2).        |
| _max\_input\_size_  | `None \| float` | Maximum input buffer (in MB) a batch pipeline can support. |
| _max\_output\_size_ | `None \| float` | Maximum output buffer (in MB) a batch pipeline can support. |
| _accuracy_          | `None \| float` | Acceptable error rate between 0.0 - 1.0 (defaults to 1.0 aka 100%). |

### Returns

The method returns a dictionary containing the details of the newly created batch pipeline.
Do note the schema is similar to the one returned by the [`dispose` method](#close-a-batch-pipeline)
or the [`cancel` method](#cancel-a-batch-pipeline).

```json
{
  "object": "batch",
  "id": "uuid",
  "data": {
    "service_id": "uuid",
    "version_id": "uuid",
    "compiler_version": "Neuron_v1.13.0",
    "correlation_id": null,
    "source_system": "Spark Python SDK",
    "unique_record_key": null,
    "response_timestamp": "1970-12-03T04:56:12.186Z",
    "batch_status": "created",
    "created_by": "john.doe@coherent.global",
    "created_timestamp": "1970-12-03T04:56:12.186Z",
    "updated_timestamp": "1970-12-03T04:56:12.186Z",
    "service_uri": "my-folder/my-service[0.4.2]"
  }
}
```

> [!TIP]
> It is recommended that you close the batch pipeline once you have finished processing
> the data. This will help free up resources and ensure optimal performance.

## Define a client-side batch pipeline by ID

This method performs no action on the batch pipeline (no API call). Instead, it
allows you to define a client-side reference for the batch pipeline using its
unique identifier (`id`), which can then be used to perform various operations
without having to specify it repeatedly in each method call.

### Arguments

The expected argument is the batch pipeline's unique identifier as a string.
At this stage, no checks are performed to validate the provided `id`.

```py
pipeline = spark.batches.of('uuid')
```

### Returns

The method returns a batch `Pipeline` object that can be used to perform subsequent
actions on the batch pipeline.

Apart from the convenience of not having to specify the batch ID repeatedly, some other
perks of using this object include the ability to build statistics and insights
about the batch pipeline. For instance, if you've built a mechanism for repeatedly
pushing and pulling data, you may retrieve details such as the total number of
records processed, the state of the pipeline, and so on.

```py
print(pipeline.state) # 'open' (or 'closed' or 'cancelled')
print(pipeline.stats) # { 'chunk_uuid_1': 123, 'chunk_uuid_2': 456 }
```

Additionally, this `Pipeline` object keeps track of chunk IDs, which are essential
for sorting and filtering data when processing multiple chunks. This object can
autogenerate chunk IDs if they are missing and handle duplicates to avoid collisions.

## Get the details of a batch pipeline

### Arguments

This method does not require any arguments. It will fetch the details of the batch
pipeline that was previously defined using the `of(id)` method.

```py
pipeline.get_info()
```

### Returns

The method returns a dictionary containing detailed information on a batch pipeline
that's been recently created.

```json
{
  "object": "batch",
  "id": "uuid",
  "data": {
    "service_id": "uuid",
    "version_id": "uudi",
    "compiler_version": "Neuron_v1.13.0",
    "correlation_id": "uuid",
    "source_system": "Spark Python SDK",
    "unique_record_key": null,
    "summary": {
      "chunks_submitted": 123,
      "chunks_retried": 0,
      "chunks_completed": 122,
      "chunks_failed": 1,
      "records_retried": 1,
      "input_size_bytes": 0,
      "output_size_bytes": 0,
      "avg_compute_time_ms": 13,
      "records_submitted": 456,
      "records_failed": 0,
      "records_completed": 450,
      "compute_time_ms": 13,
      "batch_time_ms": 12234
    },
    "configuration": {
      "initial_workers": 10,
      "chunks_per_request": 1,
      "runner_thread_count": 1,
      "acceptable_error_percentage": 0,
      "input_buffer_allocated_bytes": 70000000,
      "output_buffer_allocated_bytes": 80000000,
      "max_workers": 3000
    },
    "response_timestamp": "1970-12-03T04:56:12.186Z",
    "batch_status": "in_progress",
    "created_by": "john.doe@coherent.global",
    "created_timestamp": "1970-12-03T04:56:12.186Z",
    "updated_timestamp": "1970-12-03T04:56:12.186Z",
    "service_uri": "my-folder/my-service[0.4.2]"
  }
}
```

## Get the status of a batch pipeline

### Arguments

This method does not require any arguments. It will fetch the status of the batch
pipeline that was previously defined using the `of(id)` method.

```py
pipeline.get_status()
```

### Returns

The method returns a dictionary containing the current status of the batch pipeline
and other relevant details, such as the number of records processed, the time taken
to process the data, and the status of the pipeline.

```json
{
  "response_timestamp": "1970-12-03T04:56:12.186Z",
  "request_timestamp": "1970-12-03T04:56:12.186Z",
  "batch_status": "in_progress",
  "pipeline_status": "idle",
  "chunks_available": 200,
  "chunks_submitted": 4000,
  "record_submitted": 1000000,
  "chunks_completed": 200,
  "records_completed": 750000,
  "compute_time_ms": 82,
  "input_buffer_used_bytes": 1048576,
  "input_buffer_remaining_bytes": 68989440,
  "output_buffer_used_bytes": 402,
  "output_buffer_remaining_bytes": 68989440,
  "workers_in_use": 173,
  "records_available": 60000
}
```

Other available statuses (i.e., `batch_status`) are:

- `created`: the batch pipeline has been created but has not yet been started.
- `in_progress`: the batch pipeline is currently processing data.
- `closed`: the batch pipeline has been closed by the user.
- `closed_by_timeout`: the batch pipeline has been closed by the system due to inactivity.
- `completed`: the batch pipeline has completed processing all the input data.
- `completed_by_timeout`: the batch pipeline has been marked as completed due to timeout.
- `failed`: the batch pipeline has failed to process the input data.
- `cancelled`: the batch pipeline has been canceled by the user.

## Add input data to a batch pipeline

This method allows you to push input data to an existing batch pipeline. The data
can be pushed in chunks, and the method will return a unique identifier for each chunk.
It is also designed to facilitate data submission in different shapes and forms.

### Arguments

The method accepts 3 mutually exclusive keyword arguments:

- `inputs`: a list of your records to be processed. This is convenient when you have
  a list of records to be processed in a single chunk. Meaning you choose to handle
  the repartitioning of the data yourself.

```py
pipeline.push(inputs=[{ 'value': 42 }, { 'value': 43 }])
```

- `data`: an object of `ChunkData` type. Sometimes, you may want to perform certain
  operations, such as applying aggregations to the output data post-processing. This
  class lets you specify the `inputs`, `parameters` and `summary` separately.

```py
from cspark.sdk import ChunkData

data = ChunkData(
    inputs=[{'value': 42}, {'value': 43}],
    parameters={'common': 40},
    summary={'ignore_error': False, 'aggregation': [{'output_name': 'total', 'operator': 'SUM'}]},
)
pipeline.push(data=data)
```

- `chunks`: an object of `BatchChunk` type. This gives you full control over the
  chunk creation process, allowing you to specify the `inputs`, `parameters`,
  and `summary`, and indicate the `id` and `size`.

```py
from cspark.sdk import BatchChunk, ChunkData

chunk = BatchChunk(
    id='uuid',
    size=2,
    data=ChunkData(
        inputs=[{'value': 42}, {'value': 43}],
        parameters={'common': 40},
        summary={'ignore_error': False, 'aggregation': [{'output_name': 'total', 'operator': 'SUM'}]},
    ),
)
pipeline.push(chunks=[chunk])
```

Alternatively, you may use a helper function to create chunks and partition the data
evenly across the chunks.

```py
from cspark.sdk import create_chunks

chunks = create_chunks(inputs=[{'value': 42}, {'value': 43}, {'value': 44}], chunk_size=2)
pipeline.push(chunks=chunks)
```

### Returns

When successful, the method returns a dictionary containing the same info as the
[`get_status` method](#get-the-status-of-a-batch-pipeline), but with updated values
reflecting the new data that was pushed.

```json
{
  "response_timestamp": "1970-12-03T04:56:12.186Z",
  "request_timestamp": "1970-12-03T04:56:12.186Z",
  "batch_status": "in_progress",
  "pipeline_status": "idle",
  "chunks_available": 2,
  "chunks_submitted": 2,
  "record_submitted": 7,
  "chunks_completed": 2,
  "records_completed": 7,
  "compute_time_ms": 8,
  "input_buffer_used_bytes": 0,
  "input_buffer_remaining_bytes": 70000000,
  "output_buffer_used_bytes": 402,
  "output_buffer_remaining_bytes": 79999598,
  "workers_in_use": 1,
  "records_available": 7
}
```

## Retrieve the output data from a batch pipeline

Once you submit the input data, the batch pipeline will automatically start processing it.
Eventually, the pipeline will produce some output data, which can be pulled once available.

> [!TIP]
> You do not have to wait for the previous chunk to be processed before submitting
> the next one. Spark will automatically queue and process the chunks once the
> resources are available. A good practice is monitoring the batch pipeline's
> status and ensuring the input and output buffers are not full

### Arguments

This method accepts an optional integer argument `max_chunks` to specify the maximum
number of chunks to pull. If not provided, it will pull up to 100 available chunks
of output data.

```py
pipeline.pull(max_chunks=2)
```

### Returns

If no chunks are available to pull, the method will return the status of the batch
pipeline. Otherwise, it will return the output data for each chunk and any warnings
or errors that may have occurred during processing. The current status of the batch
pipeline will also be included in the response.

```json
{
  "data": [
    {
      "id": "uuid",
      "summary_output": [[]],
      "outputs": [{ "value": 42 }, { "value": 43 }],
      "warnings": [null, null],
      "errors": [null, null],
      "process_time": [1, 1],
    },
    {
      "id": "uuid",
      "summary_output": [[]],
      "outputs": [{ "value": 44 }, { "value": 45 }, { "value": 46 }],
      "warnings": [null, null, null],
      "errors": [null, null, null],
      "process_time": [1, 1, 1],
    }
  ],
  "status": {
    "response_timestamp": "1970-12-03T04:56:12.186Z",
    "request_timestamp": "1970-12-03T04:56:12.186Z",
    "batch_status": "in_progress",
    "pipeline_status": "idle",
    "chunks_available": 0,
    "chunks_submitted": 2,
    "record_submitted": 5,
    "chunks_completed": 2,
    "records_completed": 5,
    "compute_time_ms": 8,
    "input_buffer_used_bytes": 0,
    "input_buffer_remaining_bytes": 70000000,
    "output_buffer_used_bytes": 0,
    "output_buffer_remaining_bytes": 80000000,
    "workers_in_use": 0,
    "records_available": 0
  }
}
```

Find out more about the output data structure in the
[API reference](https://docs.coherent.global/spark-apis/batch-apis#sample-response-3).

## Close a batch pipeline

Once you have finished processing all your input data, it is important to close
the batch pipeline to free up resources and ensure optimal performance.

After you close a batch, any pending chunks will still be processed and can be retrieved.
However, you won't be able to submit new chunks to a closed batch pipeline. The
SDK maintains an internal state of the batch pipeline and will generate an error
if you try to perform an unsupported operation on it.

### Arguments

This method does not require any arguments. It will close the batch pipeline that
was previously defined using the `of` method.

```py
pipeline.dispose()
```

> [!WARNING]
> Do **NOT** use the `close()` method to close a batch pipeline. This method is
> reserved for closing the HTTP client of the `Pipeline` API resource and should not
> be used to close a batch pipeline. If that happens unintentionally, you will need
> to start over and build a new client-side pipeline using `Batches.of(id)`, which
> also means you'll lose the internal states handled by the old `Pipeline` object.

Keep in mind that if the batch pipeline has been idle for longer than 30 minutes,
it will automatically be closed by the system to free up resources, i.e., releasing
the workers and buffers.

### Returns

```json
{
  "object": "batch",
  "id": "uuid",
  "data": {
    "service_id": "uuid",
    "version_id": "uuid",
    "compiler_version": "Neuron_v1.13.0",
    "correlation_id": null,
    "source_system": "Spark Python SDK",
    "unique_record_key": null,
    "response_timestamp": "1970-12-03T04:56:12.186Z",
    "batch_status": "closed",
    "created_by": "john.doe@coherent.global",
    "created_timestamp": "1970-12-03T04:56:12.186Z",
    "updated_timestamp": "1970-12-03T04:56:12.186Z",
    "service_uri": "my-folder/my-service[0.4.2]"
  }
}
```

## Cancel a batch pipeline

There may be occasions when you need to cancel a batch pipeline before it completes
processing all the input data. This could be due to an error in the data, a change
in requirements, or any other reason that requires stopping the processing. This
method allows you to cancel a batch pipeline and free up resources.

By canceling a batch pipeline, you agree to discard all the data (pending inputs
and not consumed outputs) that has been pending. The system will stop processing
the data immediately, and you will not be able to retrieve any output data for
the canceled chunks.

### Arguments

This method does not require any arguments. It will cancel the batch pipeline that
was previously defined using the `of` method.

```py
pipeline.cancel()
```

### Returns

Similar to the `dispose` method, the `cancel` method will return a dictionary
containing the details of the batch pipeline that was canceled.

```json
{
  "object": "batch",
  "id": "uuid",
  "data": {
    "service_id": "uuid",
    "version_id": "uuid",
    "compiler_version": "Neuron_v1.13.0",
    "correlation_id": null,
    "source_system": "Spark Python SDK",
    "unique_record_key": null,
    "response_timestamp": "1970-12-03T04:56:12.186Z",
    "batch_status": "cancelled",
    "created_by": "john.doe@coherent.global",
    "created_timestamp": "1970-12-03T04:56:12.186Z",
    "updated_timestamp": "1970-12-03T04:56:12.186Z",
    "service_uri": "my-folder/my-service[0.4.2]"
  }
}
```

---

# Workflow Example

The content above describes the building blocks of the [Batches API][batch-apis]
and its potential for efficiently processing large data volumes. How you choose
to use it is contingent upon specific requirements and the characteristics of the
data being handled.

To further illustrate the practical implementation of the Batches API, consider the
following example: the `create_and_run` script. This self-contained script serves
as a demonstration of how to harmoniously use the various methods of the Batches API
within a workflow. The script's primary objective is to showcase a simple workflow
that involves reading a dataset from a JSON file, pushing it to a batch pipeline,
retrieving the output data from the pipeline, and displaying the pipeline's status at
different stages. The script will continue to execute until all data has been processed
(unless an error occurs) and the batch pipeline is closed.

```py
#!/usr/bin/env python
import json
import time

import cspark.sdk as Spark
from dotenv import load_dotenv

def create_and_run(batches: Spark.Batches):
    def print_status(status, msg):
        """Convenience function to print the status of the batch pipeline."""
        a, b, c = status['records_available'], status['record_submitted'], status['records_completed']
        print(f'{msg} :: {a} of {b} records submitted ({c} processed)')

    # START: Main workflow
    chunks = []
    with open('path/to/data.json', 'r') as f:
        data = json.load(f)
        chunks = Spark.create_chunks(data, chunk_size=200)

    if len(chunks) == 0:
        print('no data to process')
        return

    batch = batches.create('my-folder/my-service')
    print('batch created', batch.data)

    if not isinstance(batch.data, dict):
        return

    pipeline = batches.of(batch.data['id'])
    try:
        submission = pipeline.push(chunks=chunks)
        print('submission data', submission.data)
        time.sleep(1)

        status = pipeline.get_status().data
        print_status(status, 'first status check')

        while status['records_completed'] < status['record_submitted']:
            status = pipeline.get_status().data
            print_status(status, 'subsequent status check')

            if status['records_available'] > 0:
                result = pipeline.pull()
                print('result data', result.data)

            time.sleep(2) # check every 2 seconds
    except Exception as e:
        print(e)
    finally:
        state = pipeline.dispose()
        print(state.data)
        print('done!')
    # END: Main workflow

if __name__ == '__main__':
    # load Spark settings from .env file
    load_dotenv()

    # create a Spark client
    spark = Spark.Client()
    with spark.batches as b:
        create_and_run(b)
```

> [!IMPORTANT]
> The script above is a sample workflow and is not intended to be used as-is in a
> production environment. It is meant to provide you with a starting point to build
> your own workflow that suits your specific requirements.
>
> If you were to "productionize" this script, you would need to add graceful error handling,
> logging, and other features to make it more robust and reliable. You may also want
> to consider how you read and feed the input data to the pipeline and how to handle
> the output data that is returned.

Happy coding! 🚀

[Back to top](#batches-api)

<!-- References -->
[batch-apis]: https://docs.coherent.global/spark-apis/batch-apis
