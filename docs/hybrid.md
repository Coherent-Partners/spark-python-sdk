# cspark.wasm

[![PyPI version][version-img]][version-url]

This Coherent Spark Python SDK also provides a convenient way to interact with the
[Hybrid Runner][hybrid-runner] API.

> This guide assumes that you are familiar with Coherent Spark's hybrid deployments.
> Otherwise, visit the [User Guide][user-guide] to learn more about it.

## Installation

`cspark.wasm` is a module within [`cspark`][cspark] that extends `cspark.sdk` to
support the Hybrid Runner API. To install it, run:

```bash
pip install cspark
```

Hybrid runners offer a smaller subset of functionality compared to the SaaS API.
However, extending `cspark.sdk` to support the Hybrid Runner API is a good way
to keep the codebase consistent and maintainable. This also means that you may
want to check its [documentation][cspark] to learn about its client options,
error handling, and other features.

## Usage

To interact with the Hybrid Runner API, create a `Hybrid.Client` that points to the
runner's base URL (by default: `http://localhost:3000`).
Depending on your hybrid runner's configuration, you may or may not need to use
[authentication](./wasm/authentication.md).

```python
from cspark.sdk import SparkError
from cspark.wasm import Client

def main():
    try:
        with Client(tenant='my-tenant', token='open') as hybrid: # no authentication
            response = hybrid.services.execute('my-folder/my-service', inputs={'value': 42})
            print(response.data)
    except SparkError as e:
        print(e)

if __name__ == "__main__":
    main()
```

`AsyncClient` can be used similarly to the `Client` class. Explore the [examples]
and [docs] folders to find out more about its capabilities.

<!-- References -->

[cspark]: https://pypi.org/project/cspark/
[version-img]: https://img.shields.io/pypi/v/cspark
[version-url]: https://pypi.python.org/pypi/cspark
[user-guide]: https://docs.coherent.global/hybrid-runner/introduction-to-the-hybrid-runner
[hybrid-runner]: https://github.com/orgs/Coherent-Partners/packages/container/package/nodegen-server
[examples]: https://github.com/Coherent-Partners/spark-python-sdk/blob/main/examples/hybrid.py
[docs]: https://github.com/Coherent-Partners/spark-python-sdk/blob/main/docs/wasm/readme.md
