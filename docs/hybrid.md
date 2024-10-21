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
base URL of the runner. By default, the base URL is `http://localhost:3000`. You may
choose to use authentication or not, depending on how your runner is configured.

```python
import cspark.wasm as Hybrid

hybrid = Hybrid.Client(base_url='http://localhost:8080', tenant='my-tenant', token='open')
```

| Verb                                              | Description                                        |
| ------------------------------------------------- | -------------------------------------------------- |
| `Hybrid.Client.health_check([base_url])`          | [Health check](#health-check).                     |
| `Hybrid.Client.get_version([base_url])`           | [Version check](#version-check).                   |
| `Hybrid.services.upload(file, [options])`         | [Upload a WASM package](#upload-a-wasm-package).   |
| `Hybrid.services.execute(uri, [inputs, options])` | [Execute a WASM service](#execute-a-wasm-service). |

## Health check

This method allows you to check the health of a running Hybrid Runner.

```python
import cspark.wasm as Hybrid

health = Hybrid.Client.health_check()
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

version = Hybrid.Client.get_version()
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
This package refers to the zip file exported from the SaaS using `onpremises` mode via
Export API.

> [!NOTE]
> If your running instance of the runner relies on the Automatic WASM pull, there
> is no need to use this method as the runner will automatically download the
> WASM package from the SaaS.

### Arguments

| Property     | Type          | Description                                              |
| ------------ | ------------- | -------------------------------------------------------- |
| _file_       | `BinaryIO`    | The binary file (e.g., `open('path/to/file.zip', 'rb')`).|
| _file\_name_ | `None \| str` | The name of the file (defaults to 'package.zip').        |

```python
import cspark.wasm as Hybrid

upload = Hybrid.services.upload(file=open('path/to/wasm_package.zip', 'rb'))
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

This method allows you to execute a WASM service locally using Hybrid.

### Arguments

The method accepts a string or a `UriParams` object for the service URI, and optional keyword
arguments for inputs and metadata. The arguments are similar to those of the regular
`Spark.services.execute()` method used for SaaS-based APIs.

| Property             | Type          | Description                                      |
| -------------------- | ------------- | ------------------------------------------------ |
| _uri_                | `str \| UriParams` | The service URI or UriParams object.        |
| _inputs_             | `None \| str \| Dict \| List` | The input data (single or many). |
| _encoding_           | `None \| str` | The encoding to use for the request.             |
| _response\_format_   | `None \| str` | The desired response format.                     |
| _active\_since_      | `None \| str` | The transaction date (helps pinpoint a version). |
| _source\_system_     | `None \| str` | The source system.                               |
| _correlation\_id_    | `None \| str` | The correlation ID.                              |
| _call\_purpose_      | `None \| str` | The call purpose.                                |
| _compiler\_type_     | `None \| str` | The compiler type.                               |
| _subservices_        | `None \| str \| List[str]` | The list of sub-services to output. |
| _debug\_solve_       | `None \| bool`| Enable debugging for solve functions.            |
| _echo\_inputs_       | `None \| bool`| Whether to echo the input data.                  |
| _tables\_as\_array_  | `None \| str \| List[str]` | Filter which table to output as JSON array. |
| _selected\_outputs_  | `None \| str \| List[str]` | Select which output to return.      |
| _outputs\_filter_    | `None \| str` | Use to perform advanced filtering of outputs.    |

```python
import cspark.wasm as Hybrid

Hybrid.services.execute('my-folder/my-wasm-service', inputs={'my_input': 42})
```

### Returns

This method returns the output data of the WASM service execution in the same format
as the regular `Spark.services.execute()` method used for SaaS-based APIs.

[Back to top](#hybrid-deployments)

[user-guide]: https://docs.coherent.global/integrations/how-to-deploy-a-hybrid-runner
[hybrid-runner]: https://github.com/orgs/Coherent-Partners/packages/container/package/nodegen-server
