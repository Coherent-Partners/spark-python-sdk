<!-- markdownlint-disable-file MD024 -->

# Hybrid Deployments

> This reference assumes that you are familiar with Coherent Spark's hybrid
> deployments. Otherwise, visit the [User Guide][user-guide] site to learn more
> about it.

The SDK also provides a way to interact with the [Hybrid Runner][hybrid-runner] API.

Assuming that you have a hybrid deployment setting, you may use the following methods
to perform certain tasks on a runner. Obviously, a runner offers a smaller subset of
functionality compared to the SaaS API, which revolves around the ability to execute
services locally or in restricted environments.

To access the Hybrid Runner API, you need to initialize a client that points to the
base URL of the runner. By default, the base URL is `http://localhost:3000` and can be
read as an environment variable `CSPARK_RUNNER_URL`.

You may choose to use authentication or not, depending on how your runner is configured.

```python
import cspark.wasm as Hybrid

hybrid = Hybrid.Client(base_url='http://localhost:8080', tenant='my-tenant', token='open')
```

> `token: 'open'` is used to express open authorization. Otherwise, the SDK will throw
> an error if the token is not provided.

| Verb                                      | Description                                               |
| ----------------------------------------- | --------------------------------------------------------- |
| `Hybrid.health.check()`                   | [Health check](#health-check).                            |
| `Hybrid.version.get()`                    | [Check the Neuron compatibility version](#version-check). |
| `Hybrid.services.upload(file, [options])` | [Upload a WASM package](#upload-a-wasm-package).          |
| `Hybrid.services.execute(uri, [params])`  | [Execute a WASM service](#execute-a-wasm-service).        |

## Health check

This method allows you to check the health of a running Hybrid Runner.

```python
import cspark.wasm as Hybrid

health = Hybrid.Client.health_check() # will use default base URL
# or
health = Hybrid.Client.health_check('http://localhost:8080')
print(health.data)
```

Alternatively, you can use the `Hybrid.health.check()` method directly from the client instance.

```python
import cspark.wasm as Hybrid

hybrid = Hybrid.Client(tenant='my-tenant', token='open')

health = hybrid.health_check()
print(health.data)
```

### Returns

```json
{"msg": "ok"}
```

## Version check

This method allows you to check the neuron compatibility version of a running Hybrid Runner.

```python
import cspark.wasm as Hybrid

version = Hybrid.Client.get_version() # will use default base URL
# or
version = Hybrid.Client.get_version('http://localhost:8080')
print(version.data)
```

Alternatively, you can use the `Hybrid.version.get()` method directly from the client instance.

```python
import cspark.wasm as Hybrid

hybrid = Hybrid.Client(tenant='my-tenant', token='open')

version = hybrid.get_version()
print(version.data)
```

### Returns

```json
{
  "lastPullDate": "2024-05-07T03:43:46.333Z",
  "filehash": "d2f6a43d10f9aacdb8c61f0bb6307e4ebec782ecb4f44f1194a936a9227d99f2",
  "version": "1.31.2"
}
```

## Upload a WASM package

This method allows you to upload a WASM package to a running Hybrid Runner. The zip file
should contain the compiled wasm file and other assets needed to run the service.
This package refers to the zip file exported from the SaaS using `onpremises` mode
via [Export API](https://docs.coherent.global/spark-apis/impex-apis/export).

> [!NOTE]
> If your running instance of the runner relies on the automatic WASM pull, there
> is no need to use this method as the runner will automatically download the
> WASM package from the SaaS.

### Arguments

| Property     | Type          | Description                                              |
| ------------ | ------------- | -------------------------------------------------------- |
| _file_       | `BinaryIO`    | The binary file (e.g., `open('path/to/file.zip', 'rb')`).|
| _file\_name_ | `None \| str` | The name of the file (defaults to 'package.zip').        |

```python
import cspark.wasm as Hybrid

hybrid = Hybrid.Client(tenant='my-tenant', token='open')
upload = hybrid.services.upload(file=open('path/to/wasm_package.zip', 'rb'))
print(upload.data)
```

### Returns

When successful, this method returns a JSON payload containing the uploaded
service information such as the tenant, the service details, the input and output
tables, and the version ID.

```json
{
  "response_data": [
    {
      "tenant": "my-tenant",
      "services": [
        {
          "EffectiveStartDate": "1970-12-03T04:56:56.186Z",
          "EffectiveEndDate": "1980-12-03T04:56:56.186Z",
          "EngineInformation": {
            "FileSize": 592696,
            "Author": "john.doe@coherent.global",
            "ProductName": "my-folder",
            "Revision": "0.2.0",
            "Description": null,
            "FileMD5Hash": "hash-info",
            "UniversalFileHash": null,
            "ReleaseDate": "1970-12-03T04:56:56.186Z",
            "ServiceName": "my-service",
            "NoOfInstance": 1,
            "UploaderEmail": "john.doe@coherent.global",
            "DefaultEngineType": "Neuron",
            "OriginalFileName": "my-service.xlsx",
            "SizeOfUploadedFile": 592696,
            "ReleaseNote": null,
            "IsTypeScriptFile": false,
            "EngineUpgradeType": "minor",
            "PublicAPI": false,
            "FileGuid": "uuid",
            "ServiceGuid": "uuid",
            "ServiceVersionGuid": "uuid",
            "BaseUrl": "https://excel.my-env.coherent.global",
            "Tenant": "my-tenant",
            "AllowToStoreHistory": true,
            "CalcMode": "AUTO",
            "ForceInputsWriteBeforeCalcModeChanges": true,
            "Provenance": null,
            "VersionLabel": null,
            "ExplainerType": "",
            "IsXParameter": false,
            "ParametersetCompatibilityGroup": "",
            "XParameterSetVersionId": "",
            "VersionUpgradeAssert": "OFF",
            "XReportRanges": null,
            "Tags": null,
            "OriginalServiceHash": "hash-info",
            "CompiledOutputHash": "hash-info",
            "CompilerVersion": "Neuron_v1.12.0",
            "CompilerVersionServiceUpdate": "StableLatest",
            "DirectAddressingOutputsEnabled": false
          },
          "XInputTable": [
            {
              "Input Name": "my_input_1",
              "Description": null,
              "Address": "F6"
            },
            {
              "Input Name": "my_input_2",
              "Description": null,
              "Address": "F7"
            },
            {
              "Input Name": "my_input_3",
              "Description": null,
              "Address": "F5"
            }
          ],
          "XOutputTable": [
            {
              "Output Name": "my_output_1",
              "Description": null,
              "Address": "C8"
            },
            {
              "Output Name": "my_output_2",
              "Description": null,
              "Address": "B14:B115"
            }
          ],
          "VersionId": "uuid",
          "HasSignatureChain": null
        }
      ]
    }
  ]
}
```

The service information can be used to identify the service to be executed. For example,
the `version_id` or a combination of `folder` (i.e. `ProductName`), `service` (i.e. `ServiceName`),
and `version` (i.e. `Revision`) can be used to execute the service with the `execute()` method.

## Execute a WASM service

This method allows you to execute a WASM service using a Hybrid runner instance.

Similarly to the Spark API, the Hybrid Runner API supports two versions of Execute API: `v3`
(or [v3 format][v3-format]) and `v4` ([v4 format][v4-format]), which are used respectively
for single inputs and multiple inputs data formats.
By default, the SDK will return the output data in the [v4 format][v4-format]
unless you prefer to work with the original format emitted by the API.

Check out the [API reference](https://docs.coherent.global/spark-apis/execute-api)
to learn more about Services API.

### Arguments

The method accepts a string or a `UriParams` object for the service URI, and optional keyword
arguments for inputs and metadata. The arguments are similar to those of the regular
[`Spark.services.execute(uri, [**params])`][sdk-service-execute] method used for the
SaaS-based API in [cspark.sdk][sdk].

Keep in mind that the Hybrid Runner API does not support all the features of the SaaS API.
Its primary objective is to execute a Neuron-based service locally or in a restricted environment.
As a result, most of the metadata will be ignored by the runner.

For the first argument, the service URI locator as a `string` or `UriParams` object:

| Property     | Type           | Description                                      |
| -----------  | -------------- | ------------------------------------------------ |
| _folder_     | `None \| str`  | The folder name.                                 |
| _service_    | `None \| str`  | The service name.                                |
| _version_    | `None \| str`  | The user-friendly semantic version of a service. |
| _version\_id_| `None \| str`  | The UUID of a particular version of the service. |
| _service\_id_| `None \| str`  | The service UUID (points to the latest version). |

For the other keyword arguments:

| Property             | Type          | Description                                      |
| -------------------- | ------------- | ------------------------------------------------ |
| _inputs_             | `None \| str \| Dict \| List` | The input data (single or many). |
| _response\_format_   | `original \| alike` | Response data format to use (defaults to `alike`).|
| _encoding_           | `gzip \| deflate`   | Compress the payload using this encoding. |
| _active\_since_      | `None \| str` | The transaction date (helps pinpoint a version). |
| _source\_system_     | `None \| str` | The source system (defaults to `Spark Python SDK`).|
| _correlation\_id_    | `None \| str` | The correlation ID.                              |
| _call\_purpose_      | `None \| str` | The call purpose.                                |
| _tables\_as\_array_  | `None \| str \| List[str]`| Filter which table to output as JSON array.|
| _debug\_solve_       | `None \| bool`| Enable debugging for solve functions.            |
| _selected\_outputs_  | `None \| str \| List[str]`| Select which output to return.       |
| _outputs\_filter_    | `None \| str` | Use to perform advanced filtering of outputs .   |
| _echo\_inputs_       | `None \| bool`| Whether to echo the input data (alongside the outputs). |
| _subservices_        | `None \| str \| List[str]`| The list of sub-services to output.  |

```python
import cspark.wasm as Hybrid

hybrid = Hybrid.Client(tenant='my-tenant', token='open')
response = Hybrid.services.execute('my-folder/my-service', inputs={'value': 42}, response_format='original')
print(response.data)
```

### Returns

This method returns the output data of the WASM service execution in the same format
as the regular [`Spark.services.execute(uri, [**params])`][sdk-service-execute]
method used for the SaaS-based API in [cspark.sdk][sdk].

[Back to top](#hybrid-deployments)

<!-- References -->
[sdk]: https://pypi.org/project/cspark/
[user-guide]: https://docs.coherent.global/hybrid-runner/introduction-to-the-hybrid-runner
[hybrid-runner]: https://github.com/orgs/Coherent-Partners/packages/container/package/nodegen-server
[sdk-service-execute]: https://github.com/Coherent-Partners/spark-python-sdk/blob/main/docs/services.md#execute-a-spark-service
[v3-format]: https://docs.coherent.global/spark-apis/execute-api/execute-api-v3
[v4-format]: https://docs.coherent.global/spark-apis/execute-api/execute-api-v4
