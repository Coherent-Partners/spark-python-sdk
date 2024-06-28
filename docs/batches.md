<!-- markdownlint-disable-file MD024 -->

# Batch API

| Verb                                      | Description                            |
| ----------------------------------------- | -------------------------------------- |
| `Spark.batches.create(params, [options])` | Create a new batch pipeline.           |
| `Spark.batches.of(id)`                    | Sets the batch pipeline ID to be used in subsequent operations. |
| `Spark.batches.of(id).get()`              | Get the details of the batch pipeline. |
| `Spark.batches.of(id).get_status()`       | Get the status of the batch pipeline.  |
| `Spark.batches.of(id).push(data)`         | Add input data to the batch pipeline.  |
| `Spark.batches.of(id).pull([options])`    | Retrieve the output data from the batch pipeline. |
| `Spark.batches.of(id).close()`            | Close the batch pipeline.              |
| `Spark.batches.of(id).cancel()`           | Cancel the batch pipeline.             |

> NOTE: Note: Currently being developed. Please check back soon for updates.
