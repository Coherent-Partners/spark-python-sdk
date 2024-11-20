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

- [Execute Records Sequentially using Execute APIv3](api_v3_for_loop/readme.md)
- [Execute Sync Batch of Records using Execute APIv4](api_v4_sync_batch/readme.md)
- [Service Promotion](service_promotion/readme.md)
- [Asynchronous Batch Processing](async_batch/readme.md)

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
them out. Follow [this guide][hybrid-runner] if you need help setting up the hybrid
runner.

[Back to top](#common-use-cases) or go to [Execute Records Sequentially using Execute APIv3](api_v3_for_loop).

<!-- References -->
[contributing-url]: https://github.com/Coherent-Partners/spark-python-sdk/blob/main/CONTRIBUTING.md
[hybrid-runner]: https://github.com/Coherent-Partners/spark-python-sdk/blob/main/docs/wasm/readme.md
[poetry]: https://python-poetry.org/
[rye]: https://rye-up.com/
