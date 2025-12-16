<!-- markdownlint-disable-file MD029 -->
# Common Use Cases

This folder contains a collection of common use cases that developers might have to
deal with on a regular basis when working with Coherent Spark. These use cases serve
as a reference and starting point for users building their own applications, providing
foundational examples that can be expanded into more complex solutions.

Each use case is a standalone Python project showcasing how to utilize the SDK
to achieve specific outcomes. The examples are categorized by their operations,
including data ingestion, data processing, and data export.

## Use Cases

- [Execute records sequentially](api_v3_for_loop/readme.md)
- [Execute batch of records synchronously](api_v4_sync_batch/readme.md)
- [Asynchronous batch processing](async_batch/readme.md)
- [Promote services across tenants or environments](service_promotion/readme.md)
- [Validate JWTs against Keycloak](token_validation/readme.md)
- [Bulk upload services to Spark](bulk_upload/readme.md)

## How to Run Use Cases

To run a use case, you need to download the use case folder with its underlying
content. Then, use [Poetry][poetry] to install the dependencies and run the
Python scripts.

> [!NOTE]
> Follow the instructions on [Poetry's website](https://python-poetry.org/docs/)
> to install it on your machine if you haven't done so already. If you cloned this
> repository and set up your development environment with [Rye], [Poetry] will be
> installed automatically as a development dependency.

1. install the dependencies

```bash
poetry install
```

2. replace the placeholders in the `main.py` file with your own values (usually Spark settings)

3. run the use case

```bash
poetry run python main.py
```

If you encounter any issues, please refer to the use case's readme file for more
information on how to troubleshoot and resolve them.

## Development Environment

Start by cloning the repository and installing the dependencies. Then, follow
[this guide][contributing-url] to set up your development environment.

Though [Rye] is used for virtual environments, dependency management and packaging
for the codebase, you will need to use [Poetry] to run these examples. Once the setup
is complete, you can run the use cases as described above. Remember to navigate to
the desired use case folder to get started.

## Hybrid Runner

To make it easy to test some of the examples, we provide a "[volume of cylinder](volume-cylinder.zip)"
compiled WebAssembly (WASM) module that can be used in hybrid deployments. This WASM is
a simple module that calculates the volume of a cylinder based on its radius and height.

Most of the use cases are based on this module, so you may use this WASM to test
them out. For example, you will first need to start your hybrid runner with the
following command:

```bash
docker run --name wasm-server -p 3000:3000 \
  -v /Users/johndoe/models:/models \
  -e MODEL_LOCATION=/models \
  -e UPLOAD_ENABLED=true \
  -e USE_SAAS=false \
  ghcr.io/coherent-partners/nodegen-server:v1.39.0
```

Then, you can use the following Python code to upload the WASM module to the
hybrid runner:

```python
import cspark.wasm as Hybrid

with Hybrid.Client(base_url='http://localhost:3000/fieldengineering', token='open') as hybrid:
    response = hybrid.services.upload(file=open('volume-cylinder.zip', 'rb'))
    print(response.data)
```

> [!TIP]
> Consider using `versionId` as service URI when working with sync batch processing
> (a.k.a Execute APIv4). It is a known issue we're working to resolve.

Once uploaded, you are ready to run use cases that play well with hybrid runners.
Remember to use `cspark.wasm.Client` for hybrid runners instead of `cspark.sdk.Client`,
which is for the SaaS-based API. Follow [this guide][hybrid-runner] if you need more
help working with hybrid runners.

## Troubleshooting

It turns out that some OSes may run into some issues when trying to use the SDK
to perform HTTP requests. A common issue is that most recent versions of Python on
Windows machines may not have the necessary SSL certificates. To fix this, you can
either:

- use a proxy server to perform the requests
- use a self-signed certificate to perform the requests
- use a certificate from a trusted authority
- or disable SSL verification (not recommended but may be okay in some cases)

For example, you can disable SSL verification by passing the `verify` option to the
`http_client` parameter of the `Spark.Client` class. That means, you will need to
provide a custom HTTP client (e.g., [httpx.Client](https://www.python-httpx.org/advanced/#custom-http-clients))

```python
import httpx
import cspark.sdk as Spark

spark_opts = {
  'base_url': 'https://spark.my-env.coherent.global/my-tenant',
  'token': 'Bearer my-access-token',
  'http_client': httpx.Client(verify=False) # this 'verify=False' disables SSL verification
}
with Spark.Client(**spark_opts) as spark:
    response = spark.services.execute('my-folder/my-service', inputs={'value': 42})
    print(response.data)
```

> [!TIP]
> It's always a good idea to double-check with your IT department to see if they have any
> restrictions on your network/environment/account that may prevent you from using the SDK.

[Back to top](#common-use-cases) or go to [Execute Records Sequentially](api_v3_for_loop).

<!-- References -->
[contributing-url]: https://github.com/Coherent-Partners/spark-python-sdk/blob/main/CONTRIBUTING.md
[hybrid-runner]: https://github.com/Coherent-Partners/spark-python-sdk/blob/main/docs/wasm/readme.md
[poetry]: https://python-poetry.org/
[rye]: https://rye-up.com/
