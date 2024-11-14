## Execute Records Sequentially using Execute APIv3

This execution is based on the [Execute APIv3][exec-v3] and uses a for-loop approach to submit
each record individually and sequentially. Benefits of running this type of iteration
include the generation of a call ID for each API call, which can be used to retrieve
a detailed log of the execution.

This example also assumes that the data is coming from a [inputs.json](inputs.json)
data file and will output the results to a `outputs.json` file, both in JSON format.
If you need to process CSV or other formats, you will need to adjust the `read_file(...)`
function accordingly.

Every API call will be logged to the console and saved to a `console.log` file.

> **Note**: This example can be used in hybrid deployments as well.

## Running the Example

To run this use case, replace the placeholder values with your own:

- `source_path`: Path to the data file (change the file name if needed)
- `output_path`: Path to save the output file (change the file name if needed)
- `base_url`: Base URL of the Coherent Spark instance
- `token`: Bearer token to authenticate the API calls (see [Authentication](../../../docs/authentication.md))
- `service_uri`: Locate which service to execute (folder and service name)

This should be a good starting point to understand how to execute multiple inputs
sequentially using [Execute APIv3][exec-v3]. You might want to adjust the code to
fit your specific needs. However, consider using another approach if you need to
process a larger number (1K+) of records or asynchronous calls.

<!-- References -->
[exec-v3]: https://docs.coherent.global/spark-apis/execute-api/execute-api-v3
