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

[Batch API][batch-apis] provides a series of endpoints for processing high-volume
data through Spark services. Built on a dedicated infrastructure, it enables efficient
parallel processing that automatically scales based on workload demands. This API delivers
optimal performance by dynamically adjusting computational resources to match your
data processing needs.

> [!NOTE]
> Batch API is the optimal choice for processing large datasets with over 10,000 records
> or calculations exceeding 500ms. While alternatives like the [Services API](./services.md) exist,
> the Batch APIs provide the most efficient solution for high-volume data processing unless
> specific requirements dictate otherwise.

For more information on the Batch API and its endpoints, refer to the [API reference][batch-apis].

## Describe batch pipelines across a tenant

This method provides a comprehensive overview of batch pipelines executed within a tenant.
It allows you to monitor and track both active and recently completed batches (within the
last hour). Use this method to efficiently manage and analyze your batch processing operations.

### Arguments

This method does not require any arguments.

```py
spark.batches.describe()
```

### Returns

This will only retrieve information about batches initiated by your user account unless you have
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

This method initializes a new batch pipeline, a prerequisite step for any data
processing operations.

> [!IMPORTANT]
> Store the returned pipeline `id` securely. You'll need this unique identifier
> for all subsequent operations on this pipeline.

### Arguments

The method requires a service identifier (either as a string or `UriParams` object)
and accepts optional configuration parameters for metadata and pipeline behavior
(experimental features).

For the first argument, provide the service URI as a string or `UriParams` object:

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

For the second argument, you can provide optional parameters to customize the pipeline's behavior,
including scaling and operational configurations:

| Property             | Type          | Description                                      |
| -------------------- | ------------- | ------------------------------------------------ |
| _active\_since_      | `None \| str` | The transaction date (helps pinpoint a version). |
| _source\_system_     | `None \| str` | The source system (defaults to `Spark Python SDK`).|
| _correlation\_id_    | `None \| str` | The correlation ID.                              |
| _call\_purpose_      | `None \| str` | The call purpose.                                |
| _subservices_        | `None \| str \| List[str]`| The list of subservices to output.   |
| _selected\_outputs_  | `None \| str \| List[str]`| Select which output to return.       |
| _unique\_record\_key_| `None \| str \| List[str]`| Indicate certain inputs as unique identifiers. |

The following optional arguments are **experimental** and may change in future releases.

| Property            | Type            | Description                                      |
| ------------------- | --------------- | ------------------------------------------------ |
| _min\_runners_      | `None \| int`   | Number of concurrent runners used to start a batch in a VM before ramping up (defaults to 10). |
| _max\_runners_      | `None \| int`   | Maximum number of concurrent runners allowed in a VM (defaults to 100). |
| _chunks\_per\_vm_   | `None \| int`   | Number of chunks to be processed by all VMs (defaults to 2). |
| _runners\_per\_vm_  | `None \| int`   | Number of runners per VM (defaults to 2).        |
| _max\_input\_size_  | `None \| float` | Maximum input buffer (in MB) a pipeline can support. |
| _max\_output\_size_ | `None \| float` | Maximum output buffer (in MB) a pipeline can support. |
| _accuracy_          | `None \| float` | Acceptable error rate between 0.0 - 1.0 (defaults to 1.0 aka 100%). |

### Returns

The method returns a dictionary containing the details of the newly created pipeline.
Do note that the schema is similar to the one returned by the [`dispose` method](#close-a-batch-pipeline)
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
> Remember to close the pipeline once you have finished processing the data.
> This will help free up resources and ensure optimal performance.

## Define a client-side batch pipeline by ID

This method creates a client-side reference to an existing batch pipeline using its
unique identifier (`id`). It serves as a convenient way to interact with a specific
pipeline without repeatedly providing its ID for each operation.

### Arguments

The method requires a single argument: the pipeline's unique identifier (`id`) as
a string. Note that this method does not validate the ID or make any API calls; it
simply establishes a local reference to the pipeline.

```py
pipeline = spark.batches.of('uuid')
```

### Returns

The method returns a batch `Pipeline` object that serves as an interface for all
subsequent pipeline operations.

This object provides more than just convenience in handling batch IDs. It maintains
valuable pipeline metrics and status information, enabling you to:

- Track the pipeline's current state
- Monitor the total number of processed records
- Access processing statistics
- Manage chunk operations efficiently

```py
print(pipeline.state) # 'open' (other values: 'closed' or 'cancelled')
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

The method returns a dictionary containing detailed information on a pipeline
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

The method returns a dictionary containing comprehensive pipeline metrics, including:

- Current pipeline and batch status
- Record processing counts and progress
- Computation time metrics
- Buffer utilization statistics
- Worker allocation information

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

- `created`: the pipeline has been created but has not yet been started.
- `in_progress`: the pipeline is currently processing data.
- `closed`: the pipeline has been closed by the user.
- `closed_by_timeout`: the pipeline has been closed by the system due to inactivity.
- `completed`: the pipeline has completed processing all the input data.
- `completed_by_timeout`: the pipeline has been marked as completed due to timeout.
- `failed`: the pipeline has failed to process the input data.
- `cancelled`: the pipeline has been canceled by the user.

## Add input data to a batch pipeline

This method enables bulk submission of input data to an existing pipeline. It
supports various data formats and structures to provide flexible data ingestion
options.

> [!WARNING]
> The SDK does **NOT** automatically convert regular JSON objects into JSON arrays
> when submitting to the pipeline. Submitting data in an incorrect format may result
> in unexpected behavior or processing errors, such as record count mismatches.
> Always ensure your input data is properly formatted as JSON arrays.

### Arguments

The method accepts 4 mutually exclusive keyword arguments:

- `raw`: is the dataset in its most primitive shape and can be of `string` or `bytes`
as long as it is JSON serializable.

```py
raw_string = """
{
  "chunks": [
    {
      "id": "0001",
      "size": 2,
      "data": {
        "inputs": [
          ["input_1", "input_2", "input_N"],
          [0, "zero", false],
          [1, "one", true]
        ],
        "parameters": {"common_input": 0}
      }
    }
  ]
}
"""
pipeline.push(raw=raw_string)
```

- `inputs`: is convenient when you have a list of records that needs to be processed
  in one single chunk. That means, if you need to submit multiple chunks, you will
  have to call the `push` method multiple times.

```py
pipeline.push(inputs=[['input_1', 'input_2', 'input_N'], [0, 'zero', False], [1, 'one', True]])
```

- `data`: is an object of `ChunkData` type. Sometimes, you may want to perform certain
  operations, such as applying aggregations to the output data. This
  class lets you specify the `inputs`, `parameters` and `summary` separately.

```py
from cspark.sdk import ChunkData

data = ChunkData(
    inputs=[['input_1', 'input_2', 'input_N'], [0, 'zero', False], [1, 'one', True]],
    parameters={'common': 40},
    summary={'ignore_error': False, 'aggregation': [{'output_name': 'total', 'operator': 'SUM'}]},
)
pipeline.push(data=data)
```

- `chunks`: is an object of `BatchChunk` type. This gives you full control over the
  chunk creation process, allowing you to indicate the `id` and `size` as well as
  the `inputs`, `parameters`, and `summary`.

```py
from cspark.sdk import BatchChunk, ChunkData

chunk = BatchChunk(
    id='uuid',
    size=2,
    data=ChunkData(
        inputs=[['input_1', 'input_2', 'input_N'], [0, 'zero', False], [1, 'one', True]],
        parameters={'common': 40},
        summary={'ignore_error': False, 'aggregation': [{'output_name': 'total', 'operator': 'SUM'}]},
    ),
)
pipeline.push(chunks=[chunk])
```

Alternatively, you may use a helper function to create chunks and partition the data
_evenly_ across the chunks.

```py
from cspark.sdk import create_chunks

chunks = create_chunks(
    inputs=[['input_1', 'input_2', 'input_N'], [0, 'zero', False], [1, 'one', True]],
    chunk_size=2,
)
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

After submitting input data, the pipeline begins processing automatically. Output
data becomes available progressively and can be retrieved through the pull operation.

> [!TIP]
> You can continue submitting chunks without waiting for previous ones to complete.
> Spark manages the queue and processing automatically, allocating compute resources
> as they become available. Best practice is to monitor the pipeline status periodically
> and ensure input/output buffers have sufficient capacity.

### Arguments

This method accepts an optional integer argument `max_chunks` to specify the maximum
number of chunks to pull. If not provided, it will pull down up to 100 available chunks
of output data.

```py
pipeline.pull(max_chunks=2)
```

### Returns

If no chunks are available to pull, the method will return the status of the
pipeline. Otherwise, it will return the output data for each chunk and any warnings
or errors that may have occurred during processing. The current status of the
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
      "process_time": [1, 1]
    },
    {
      "id": "uuid",
      "summary_output": [[]],
      "outputs": [{ "value": 44 }, { "value": 45 }, { "value": 46 }],
      "warnings": [null, null, null],
      "errors": [null, null, null],
      "process_time": [1, 1, 1]
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

Once all data processing is complete, it's essential to close the pipeline to release
system resources and maintain optimal performance.

After closing a batch, any pending chunks in the processing queue will still complete
and their results can be retrieved. However, the pipeline won't accept new chunk
submissions. The SDK tracks the pipeline's state internally and will throw an error
if you attempt any operations not supported on a closed pipeline.

### Arguments

This method does not require any arguments. It will close the pipeline that
was previously defined using the `of(id)` method.

```py
pipeline.dispose()
```

> [!WARNING]
> Do **NOT** use the `close()` method to close a pipeline. This method is reserved
> for closing the HTTP client of the `Pipeline` API resource. If and when
> that happens unintentionally, you will need to start over and build a new client-side
> pipeline using `Batches.of(id)`, which also means you'll lose the internal states
> handled by the old `Pipeline` object.

Note that pipelines automatically close after 30 minutes of inactivity to optimize
resource utilization. This automatic closure releases allocated workers and buffers.

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

There may be occasions when you need to cancel a pipeline before it completes
processing all the input data. This could be due to an error in the data, a change
in requirements, or any other reason that requires stopping the processing. This
method allows you to cancel a pipeline.

By canceling a pipeline, you agree to discard all the data (input and output
buffers) that has been pending. The system will stop processing any data immediately,
and you will not be able to retrieve any output data for the canceled chunks.

### Arguments

This method does not require any arguments. It will cancel the pipeline that
was previously defined using the `of(id)` method.

```py
pipeline.cancel()
```

### Returns

Similar to the `dispose` method, the `cancel` method will return a dictionary
containing the details of the canceled pipeline.

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

## Workflow Example

The content above describes the building blocks of the [Batches API][batch-apis]
and its potential for efficiently processing large data volumes. How you choose
to use it is contingent upon specific requirements and the characteristics of the
data being handled.

To further illustrate the practical implementation of the Batches API, consider the
following example: the `create_and_run()` script.

It's a self-contained script and should serve as a demonstration of how to harmoniously
use the Batches API methods. The script performs the following tasks:

- read a dataset (inputs) from a JSON file;
- push it in chunks to a newly created batch pipeline;
- check the pipeline's status every 2 seconds;
- retrieve the output data from the pipeline when available;
- and finally, close the pipeline.

The script maintains continuous interaction with Spark until all data processing
is complete. If an error occurs during execution, the pipeline will be safely
terminated and all resources properly released.

```py
import json
import time

import cspark.sdk as Spark
from dotenv import load_dotenv


def create_and_run(batches: Spark.Batches):
    logger = Spark.get_logger(context='Async Batch', datefmt='%Y-%m-%d %H:%M:%S')

    def log_status(status, msg='status check'):
        """Convenience function to print the status of the batch pipeline."""
        a, b, c = status['records_available'], status['record_submitted'], status['records_completed']
        logger.info(f'{msg} :: {a} of {b} records submitted ({c} processed)')

    chunks, results = [], []
    with open('path/to/inputs.json', 'r') as f:
        data = json.load(f)
        chunks = Spark.create_chunks(data, chunk_size=150)

    if len(chunks) == 0:
        logger.warning('no input data to process')
        return

    pipeline = None
    try:
        batch = batches.create('my-folder/my-service')
        pipeline = batches.of(batch.data['id'])
        pipeline.push(chunks=chunks)
        time.sleep(5)

        status = pipeline.get_status().data

        while status['records_completed'] < status['record_submitted']:
            status = pipeline.get_status().data
            log_status(status)

            if status['records_available'] > 0:
                result = pipeline.pull()
                log_status(result.data['status'], 'data retrieval status')

                for r in result.data['data']:
                    results.extend(r['outputs'])

            time.sleep(2)
    except Spark.SparkError as err:
        logger.error(err.message)
        logger.info(err.details)
    except Exception as exc:
        logger.critical(f'Unknown error: {exc}')
    finally:
        if pipeline:
            if pipeline.state == 'open':
                pipeline.dispose()
            pipeline.close()

        with open('path/to/outputs.json', 'w') as f:
            json.dump(results, f, indent=2)

        logger.info(f'total processed outputs: {len(results)}\nDone! 🎉')


if __name__ == '__main__':
    load_dotenv() # load Spark settings from .env file

    spark = Spark.Client(timeout=90_000, logger={'context': 'Async Batch'}) # create a Spark client
    with spark.batches as b:
        create_and_run(b)
```

> [!IMPORTANT]
> The script above is a sample workflow and is not intended to be used as-is in a
> production environment. It is meant to provide you with a starting point to build
> your own workflow (one that suits your specific requirements).
>
> If you were to "productionize" this script, you would need to add graceful error handling,
> logging, among other capabilities to make it more robust and reliable. You may also want
> to consider how you read and feed the input data to the pipeline and how to handle
> the output data once it's available.
> That said, take a look at the [async batch use case](../../examples/usecases/async_batch/)
> which is a more complete example.

The example assumes pristine input data, which is rarely the case in real applications.
When working with raw data, you'll likely need preprocessing steps. The `BatchChunk`
and `ChunkData` classes provide flexible data manipulation capabilities to ensure
your data meets pipeline requirements before processing.

[Back to top](#batches-api) or [Next: Log History API](./history.md)

<!-- References -->
[batch-apis]: https://docs.coherent.global/spark-apis/batch-apis
