<!-- markdownlint-disable-file MD024 -->

# Batch API

| Verb                                      | Description                            |
| ----------------------------------------- | -------------------------------------- |
| `Spark.batches.describe()`                | Describes the batch pipelines across a tenant.|
| `Spark.batches.create(params, [options])` | Create a new batch pipeline.           |
| `Spark.batches.of(id)`                    | Define a batch pipeline by ID.         |
| `Spark.batches.of(id).get()`              | Get the details of the batch pipeline. |
| `Spark.batches.of(id).get_status()`       | Get the status of a batch pipeline.  |
| `Spark.batches.of(id).push(data)`         | Add input data to a batch pipeline.  |
| `Spark.batches.of(id).pull([options])`    | Retrieve the output data from a batch pipeline. |
| `Spark.batches.of(id).dispose()`          | Close a batch pipeline.              |
| `Spark.batches.of(id).cancel()`           | Cancel a batch pipeline.             |

> NOTE: Currently being documented. Please check back soon for updates.
