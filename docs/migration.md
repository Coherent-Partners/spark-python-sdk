# Migration Guide: v0.2.x → v0.3.x

This guide will help you migrate your code from Coherent Spark Python SDK v0.2.x to v0.3.x.

## Overview

Version 0.3.0 introduces significant architectural improvements to the SDK:

1. **Centralized HTTP Client Management**: HTTP clients are now managed at the `Client` level instead
  of per-resource, improving resource efficiency and connection management.

2. **Asynchronous Client Support**: a new `AsyncClient` class is available for async operations,
  providing full parity with the synchronous client.

3. **Context Manager Pattern**: both synchronous and asynchronous clients now support the context
  manager pattern for proper resource cleanup.

## Key Changes

### 1. HTTP Client Architecture

#### Before (v0.2.x)

In v0.2.x, each `ApiResource` class created and managed its own HTTP client instance. This meant that
if you used multiple resources (e.g., `services`, `batches`, `folders`), each would create a separate
HTTP client, leading to:

- Multiple HTTP connections to the same server
- Inefficient resource usage
- Potential connection pool exhaustion
- Manual cleanup required for each resource

```python
# v0.2.x - Each resource managed its own HTTP client
import cspark.sdk as Spark

spark = Spark.Client(env='my-env', tenant='my-tenant', api_key='my-api-key')
with spark.services as services:
    response = services.execute('my-folder/my-service', inputs={'value': 42})

# Each resource internally created its own HTTP client
services = spark.services  # Creates HTTP client #1
batches = spark.batches    # Creates HTTP client #2
folders = spark.folders    # Creates HTTP client #3

# Manual cleanup might be needed for each resource
```

#### After (v0.3.0)

In v0.3.0, the HTTP client is created once at the `Client` level and shared across all resources.
This provides:

- Single HTTP client instance shared by all resources
- Better connection pooling and resource management
- Automatic cleanup via context manager pattern
- Improved performance and efficiency

```python
# v0.3.0 - Single HTTP client shared across all resources
import cspark.sdk as Spark

# Recommended: Use context manager for automatic cleanup
with Spark.Client(env='my-env', tenant='my-tenant', api_key='my-api-key') as spark:
    # All resources share the same HTTP client instance
    services = spark.services  # Uses shared HTTP client
    batches = spark.batches    # Uses shared HTTP client
    folders = spark.folders    # Uses shared HTTP client

    # No manual cleanup needed - context manager handles it
```

#### Migration Steps

1. **Update Client Usage**: Wrap your `Client` instantiation in a `with` statement (recommended):

```python
# Before (v0.2.x)
spark = Spark.Client(env='my-env', tenant='my-tenant', api_key='my-api-key')
response = spark.services.execute('my-folder/my-service', inputs={'value': 42})
# Manual cleanup might be needed

# After (v0.3.0) - Recommended
with Spark.Client(env='my-env', tenant='my-tenant', api_key='my-api-key') as spark:
    response = spark.services.execute('my-folder/my-service', inputs={'value': 42})
# Automatic cleanup when exiting the context
```

1. **Alternative: Manual Cleanup**: If you cannot use the context manager pattern, you can still
manually close the client:

```python
# After (v0.3.0) - Manual cleanup
spark = Spark.Client(env='my-env', tenant='my-tenant', api_key='my-api-key')
try:
    response = spark.services.execute('my-folder/my-service', inputs={'value': 42})
finally:
    spark.close()  # Explicitly close the shared HTTP client
```

1. **Custom HTTP Client**: If you were passing custom HTTP clients to individual resources, now pass
it to the `Client` constructor:

```python
# v0.3.x - Custom HTTP client at Client level
import httpx
import cspark.sdk as Spark

custom_client = httpx.Client(proxy='https://my-proxy-url', timeout=120.0)

with Spark.Client(
    env='my-env',
    tenant='my-tenant',
    api_key='my-api-key',
    http_client=custom_client  # All resources will use this client
) as spark:
    response = spark.services.execute('my-folder/my-service', inputs={'value': 42})
```

### 2. Asynchronous Client Support

#### New Feature: AsyncClient

v0.3.0 introduces `AsyncClient` for asynchronous operations, providing full API parity with the
synchronous client. Though most existing examples and documentation still use the synchronous client,
you may consider migrating to the asynchronous client for better performance and scalability.

#### Usage

```python
# v0.3.0 - Asynchronous operations
import asyncio
import cspark.sdk as Spark

async def main():
    async with Spark.AsyncClient(env='my-env', tenant='my-tenant', api_key='my-api-key') as spark:
        # All async resources share the same async HTTP client
        response = await spark.services.execute('my-folder/my-service', inputs={'value': 42})
        print(response.data)

        # Batch operations
        batch = await spark.batches.create('my-folder/my-service')
        pipeline = spark.batches.of(batch.data['id'])
        await pipeline.push(chunks=chunks)
        status = await pipeline.get_status()
        results = await pipeline.pull()

asyncio.run(main())
```

#### Available Async Resources

All resources are available in async form:

- `spark.health` → `AsyncHealth`
- `spark.folders` → `AsyncFolders`
- `spark.services` → `AsyncServices`
- `spark.transforms` → `AsyncTransforms`
- `spark.batches` → `AsyncBatches`
- `spark.logs` → `AsyncHistory`
- `spark.files` → `AsyncFiles`
- `spark.wasm` → `AsyncWasm`
- `spark.impex` → `AsyncImpEx`

#### Migration to Async

If you want to migrate synchronous code to async:

```python
# Before (v0.2.x) - Synchronous
spark = Spark.Client(env='my-env', tenant='my-tenant', api_key='my-api-key')
response = spark.services.execute('my-folder/my-service', inputs={'value': 42})

# After (v0.3.0) - Asynchronous
async with Spark.AsyncClient(env='my-env', tenant='my-tenant', api_key='my-api-key') as spark:
    response = await spark.services.execute('my-folder/my-service', inputs={'value': 42})
```

### 3. Context Manager Pattern

Both `Client` and `AsyncClient` now support the context manager pattern for proper resource cleanup.

#### Benefits

- **Automatic Cleanup**: HTTP clients are automatically closed when exiting the context
- **Exception Safety**: Resources are cleaned up even if an exception occurs
- **Best Practice**: Follows Python's resource management patterns

#### Examples

```python
# Synchronous client with context manager
with Spark.Client(env='my-env', tenant='my-tenant', api_key='my-api-key') as spark:
    response = spark.services.execute('my-folder/my-service', inputs={'value': 42})
    # Client automatically closed here

# Asynchronous client with context manager
async with Spark.AsyncClient(env='my-env', tenant='my-tenant', api_key='my-api-key') as spark:
    response = await spark.services.execute('my-folder/my-service', inputs={'value': 42})
    # Client automatically closed here
```

## Migration Checklist

- [ ] Update all `Client` instantiations to use context manager pattern (`with` statement)
- [ ] Remove any manual HTTP client cleanup code (now handled automatically)
- [ ] If using custom HTTP clients, move them to the `Client` constructor
- [ ] Consider migrating to `AsyncClient` for better performance in async contexts
- [ ] Update any code that directly accessed resource HTTP clients
- [ ] Test all API operations to ensure they work with the shared HTTP client

## Common Issues and Solutions

### Issue: "Client is already closed"

**Cause**: Trying to use a client after the context manager has exited.

**Solution**: Ensure all operations are performed within the `with` block:

```python
# ❌ Wrong
with Spark.Client(...) as spark:
    pass
response = spark.services.execute(...)  # Error: client is closed

# ✅ Correct
with Spark.Client(...) as spark:
    response = spark.services.execute(...)  # Works
```

### Issue: Multiple HTTP clients still being created

**Cause**: Creating multiple `Client` instances instead of reusing one.

**Solution**: Create a single `Client` instance and reuse it:

```python
# ❌ Wrong - Creates multiple clients
spark1 = Spark.Client(...)
spark2 = Spark.Client(...)

# ✅ Correct - Single client, multiple resources
with Spark.Client(...) as spark:
    services = spark.services
    batches = spark.batches
    folders = spark.folders
```

### Issue: Async operations blocking

**Cause**: Using synchronous client in async context or not awaiting async operations.

**Solution**: Use `AsyncClient` and properly await operations:

```python
# ❌ Wrong
with Spark.Client(...) as spark:
    response = spark.services.execute(...)  # Blocks in async context

# ✅ Correct
async with Spark.AsyncClient(...) as spark:
    response = await spark.services.execute(...)  # Non-blocking
```

## Additional Notes

- The synchronous `Client` still works without the context manager, but it's recommended to use it
  for proper resource management.
- All existing synchronous code will continue to work, but you should migrate to the context manager
  pattern for better resource management.
- The async client provides the same API as the sync client, just with `async`/`await` keywords.
- Both clients share the same configuration options and authentication methods.

## Need Help?

If you find any issues during migration, please:

1. Check this migration guide for common solutions
2. Review the [SDK documentation](./readme.md)
3. Check the [examples](../examples/) for usage patterns
4. [Open an issue](https://github.com/Coherent-Partners/spark-python-sdk/issues) on GitHub.
