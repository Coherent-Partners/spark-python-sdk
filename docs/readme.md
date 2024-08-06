# SDK Documentation

This guide should serve as a comprehensive reference for the SDK. It covers all
the verbs (or methods) and parameters available in the SDK.

Additional information can be found on [Spark's User Guide](https://docs.coherent.global).

## Table of Contents

- [Authentication](./authentication.md)
- [Services API](./services.md)
- [Batches API](./batches.md)

## Getting Started

You may notice by now that `folder` and `service` names when combined form a
base identifier to locate a resource in the Spark platform for a particular
environment and tenant. I term this _Service URI_ locator.

Given that this locator may be part of either the final URL or the request payload,
it is recommended to use plain strings (i.e., not URL-encoded) when referring to
these identifiers.
The SDK will take care of encoding them when necessary. Otherwise, you risk running
into issues when trying to locate a resource.

For instance, executing a Spark service using these identifiers

- folder: `my folder` (when encoded => `my%20folder`)
- service: `my service` (when encoded => `my%20service`)

can be tricky if they are URL-encoded. See in the example below how the URI locator
formed by these identifiers can be used in different contexts:

```py
folder  = 'my%20folder'  # encoding equivalent to 'my folder'
service = 'my%20service' # encoding equivalent to 'my service'
service_uri = f'{folder}/{service}'

# Use case 1: as part of the URL
spark.services.execute(service_uri, inputs={})

# Use case 2: as part of the payload (will fail to locate the service)
spark.services.execute(service_uri, inputs=[{}])
```

Behind the scenes, the `Use case 1` (single input) uses the URI locator as part of
the final URL to locate the service to execute. Hence, it works fine whether the
identifiers are URL-encoded or not. However, when using a list of inputs in `Use case 2`,
the method uses the URI locator as part of the payload, which will fail to locate
the service if the identifiers are URL-encoded.

## HTTP Response

The SDK is built on top of the [httpx](https://pypi.org/project/httpx) library,
which provides an elegant, feature-rich HTTP module. The SDK built a layer
on top of it to simplify the process of making HTTP requests to the Spark platform.

Presently, only the synchronous HTTP methods are supported. Hence, all the methods
under `Spark.Client()` are synchronous and return an `HttpResponse` object with
the following properties:

- `status`: HTTP status code
- `data`: Data returned by the API if any (usually JSON)
- `buffer`: Binary content returned by the API if any
- `headers`: Response headers

> [!NOTE]
> Sometimes, the SDK may return a modified version of the Spark API response for
> better readability and ease of use. Keep an eye out on the `data` property
> when accessing the response data.
>
> As a side note, we intend to leverage the asynchronous methods [in the future](./roadmap.md)
> to provide a more efficient way to interact with the Spark platform.

## HTTP Error

When attempting to communicate with the API, the SDK will wrap any sort of failure
(any error during the roundtrip) into a `SparkApiError`, which will include
the HTTP `status` code of the response and the `request_id`, a unique identifier
of the request. The most common errors are:

- `UnauthorizedError`: when the user is not authenticated/authorized
- `NotFoundError`: when the requested resource is not found
- `BadRequestError`: when the request or payload is invalid.

The following properties are available in a `SparkApiError`:

- `name`: name of the API error, e.g., `UnauthorizedError`
- `status`: HTTP status code
- `cause`: cause of the failure
- `message`: summary of the error message causing the failure
- `request_id`: unique identifier of the request (useful for debugging)
- `details`: a stringified version of `cause`.

The `cause` property will include key information regarding the attempted request
as well as the obtained response, if available.

## API Resource

The Spark platform offers a wide range of functionalities that can be accessed
programmatically via RESTful APIs. For now, the SDK only supports [Services API](./services.md)
and [Batches API](./batches.md).

Since the SDK does not cover all the endpoints in the platform, it provides a way
to cover additional endpoints. So, if there's an API resource you would like to
consume that's not available in the SDK, you can always extend this `ApiResource`
to include it.

```py
from cspark.sdk import Client, Config, ApiResource, Uri

# 1. Prepare the additional API resource you want to consume (e.g., MyResource).
class MyResource(ApiResource):
    def __init__(self, config: Config):
        super().__init__(config)

    def fetch_data(self):
        url = Uri.of(base_url=self.config.base_url.full, version='api/v4', endpoint='my/resource')
        return self.request(url, method='GET')

# 2. Build a Spark client.
spark = Client(env='my-env', tenant='my-tenant', token='bearer token')

# 3. Your custom resource relies on the Spark configuration to build the request.
with MyResource(spark.config) as my_resource:
    # 4. Use the custom resource to fetch data.
    response = my_resource.fetch_data()
    # 5. Do something with the response.
    print(response.data)
```

Did you notice the `self.config` property and the `self.request(...)` method in the
`MyResource` class? These are inherited from the `ApiResource` class and are
available for you to use in your custom resource. The `config` property contains
some other goodies like the `base_url`, which can be used to build other URLs
supported by the Spark platform.

The `Uri` class is also available to help you build the URL for your custom resource.
In this particular example, the built URL will be: `https://excel.my-env.coherent.global/my-tenant/api/v4/my/resource`.

### Error Handling

The SDK will only throw `SparkError` errors when something goes wrong. You should
always handle these errors to avoid disrupting the flow of your application.

```py
from cspark.sdk import Client, SparkError

services = Client(api_key='open').services
try:
    response = services.execute('my-folder/my-service')
    print(response.data)
except SparkError as e:
    print(e) # Handle the error instead.
finally:
    services.close()
```

## Support and Feedback

The SDK is a powerful tool that will help you interact with the Spark platform
in a more efficient and streamlined way. It is built to help you save time and
focus on what matters most: integrating Spark into your applications.

If you have any questions or need help with the SDK, feel free to create an issue
or submit a pull request following these [guidelines](../CONTRIBUTING.md).

Happy coding! 🚀

[Back to top](#sdk-documentation) or [Next: Authentication](./authentication.md)
