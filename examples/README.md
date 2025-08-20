# SDK Examples

This directory contains example code demonstrating how to use the Coherent Spark
SDK for various operations. These examples serve as a reference for implementing
different features and functionalities of the Spark platform from a client
standpoint.

## Getting Started

Assuming that you have cloned this repository, you can run any example:

1. Set up your environment as described in the [Contributing guidelines](../CONTRIBUTING.md):

   ```bash
   rye sync --all-features
   ```

2. Configure your environment:
   - Create a `.env` file in the root directory (as per the `.env.local` file)
   - Modify the Spark credentials (base URL, authorization token, etc.) to reflect
     your actual credentials.
   - Open the `examples/<example_name>.py` file
   - Set the appropriate service URI (e.g., `my-folder/my-service`) and other
     parameters as needed.

3. Run any example:

   ```bash
   python examples/<example_name>.py
   ```

> **Note** that the examples are standalone scripts that can be run independently.
> They are designed to help you get started quickly with the SDK and understand
> how to use the different features of Spark. However, if you need more detailed
> information on how to use the SDK, please refer to the [SDK documentation](../docs/README.md).

## Available Examples

**Configuration (`config.py`)** demonstrates basic SDK setup:

- Authentication and token management
- Logging configuration
- Environment variable handling
- Platform configuration retrieval

**Folders (`folders.py`)** includes examples of folder management operations:

- Folder creation and organization
- Folder category listing and management

**Services (`services.py`)** shows how to work with Spark services:

- Service creation and deployment
- Service execution and transformation
- Schema and metadata retrieval
- Service version management
- Service search and download
- Service validation and recompilation
- Service deletion

**History (`history.py`)** contains examples of how to work with API call history:

- Execution history retrieval
- History rehydration
- History download

**Batches (`batches.py`)** shows how to work with asynchronous batch processing:

- Batch creation and execution
- Batch management

**ImpEx (`impex.py`)** contains examples of service import/export operations:

- Service import/export operations
- WASM download functionality

**Hybrid (`hybrid.py`)** shows how to work with hybrid-deployed services:

- Use the `Hybrid.Client` to interact with the Hybrid Runner API
- Check the health status of a hybrid runner

## Best Practices

1. Error Handling using `Spark.SparkError`

2. Resource Management:
   - Use context managers (`with` statements) for proper resource cleanup
   - File handling includes proper closing of resources
   - Token management is handled securely

3. Configuration:
   - Use environment variables for sensitive information
   - Use `python-dotenv` to load the environment variables
   - Service URIs and paths are configurable

## Advanced Use Cases

The [use cases](./usecases/) are standalone projects that demonstrate common scenarios such as:

- [Execute records sequentially](./usecases/api_v3_for_loop/readme.md)
- [Execute batch of records synchronously](./usecases/api_v4_sync_batch/readme.md)
- [Asynchronous batch processing](./usecases/async_batch/readme.md)
- [Promote services across tenants or environments](./usecases/service_promotion/readme.md)
- [Validate JWTs against Keycloak](./usecases/token_validation/readme.md)

> [!NOTE]
>
> - Each example file can be run independently.
> - Some examples may require specific service configurations or data formats.
> - Make sure to handle errors appropriately in production environments.
> - The examples use type hints for better code clarity and IDE support.
