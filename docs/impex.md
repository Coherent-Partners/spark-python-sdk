<!-- markdownlint-disable-file MD024 -->

# ImpEx API

| Verb                    | Description                                                                       |
| ----------------------- | --------------------------------------------------------------------------------- |
| `Spark.impex.exp(data)` | [Export Spark entities (versions, services, or folders)](#export-spark-entities). |
| `Spark.impex.imp(data)` | [Import exported Spark entities into your workspace](#import-spark-entities).     |

## Export Spark entities

This method relies on the [Export API][export-api] to export Spark entities from
a tenant workspace. You may choose to export either specific versions, services
or folders, or a combination of them, which eventually are packaged up into a zip
file that will be downloaded to your local machine.

### Arguments

The expected keyword arguments are as follows:

| Property          | Type                    | Description                                                        |
| ----------------- | ----------------------- | ------------------------------------------------------------------ |
| _folders_         | `None \| list[str]`     | 1+ folder name(s).                                                 |
| _services_        | `None \| list[str]`     | 1+ service URI(s).                                                 |
| _version\_ids_    | `None \| list[str]`     | 1+ version UUID(s) of the desired service.                         |
| _file\_filter_    | `'migrate' \| 'onpremises'` | For data migration or hybrid deployments (defaults to `migrate`).  |
| _version\_filter_ | `latest \| all`         | Which version of the file to export (defaults to `latest`).        |
| _source\_system_  | `None \| str`           | Source system name to export from (e.g., `Spark Python SDK`).      |
| _correlation\_id_ | `None \| str`           | Correlation ID for the export (useful for tagging).                |
| _max\_retries_    | `None \| int`           | Maximum number of retries when checking the export status.         |
| _retry\_interval_ | `None \| float`         | Interval between status check retries in seconds.                  |

> [!NOTE]
> Remember that a service URI can be one of the following:
>
> - `{folder}/{service}[?{version}]` or
> - `service/{service_id}` or
> - `version/{version_id}`.

Check out the [API reference](https://docs.coherent.global/spark-apis/impex-apis/export#request-body)
for more information.

```python
spark.impex.exp(
  services=['my-folder/my-service[0.4.2]', 'my-other-folder/my-service-2'],
  file_filter='onpremises',
  max_retries=5,
  retry_interval=3,
)
```

### Returns

When successful, this method returns an array of exported entities, where each entity
is an `HttpResponse` object with the buffer containing the exported entity.

> [!TIP]
> This method is transactional. It will initiate an export job, poll its status
> until it completes, and download the exported files. If you need more control over
> these steps, consider using the `exports` resource directly. You may use the following
> methods:
>
> - `Spark.impex.exports.initiate(data)` creates an export job.
> - `Spark.impex.exports.get_status(job_id)` gets an export job's status.
> - `Spark.impex.exports.download(urls)` downloads the exported files as a ZIP.

## Import Spark entities

This method lets you import exported Spark entities into your workspace. Note that
only entities that were exported for data migration can be imported back into Spark.

### Arguments

The expected keyword arguments are as follows:

| Property        | Type               | Description                                                  |
| --------------- | ------------------ | ------------------------------------------------------------ |
| _file_          | `BinaryIO`         | The ZIP file containing the exported entities.               |
| _destination_   | `str \| List[str] \| Mapping[str, str] \| List[Mapping[str, str]]`| The destination service URI(s). |
| _if\_present_   | `'abort' \| 'replace' \| 'add_version'` | What to do if the entity already exists in the destination (defaults to `add_version`). |
| _source\_system_  | `None \| str`    | Source system name to export from (e.g., `Spark Python SDK`).|
| _correlation\_id_ | `None \| str`    | Correlation ID for the export (useful for tagging).          |
| _max\_retries_    | `None \| int`    | Maximum number of retries when checking the export status.   |
| _retry\_interval_ | `None \| float`  | Interval between status check retries in seconds.            |

The `destination` folder should exist in the target workspace to import the entities.
You may define how to map the exported entities to the destination tenant by providing
any of the formats indicated below:

- when `str` or `List[str]`, the SDK assumes that the destination service URIs are the same as the source service URIs.
- when `Mapping[str, str]` or `List[Mapping[str, str]]`, the SDK expects a mapping of source service URIs to destination service URIs as
  shown in the table below.

| Property  | Type    | Description                                |
| --------- | ------- | ------------------------------------------ |
| _source_  | `str`   | The service URI of the source tenant.      |
| _target_  | `str \| None`| The service URI of the destination tenant (defaults to `source`) |
| _upgrade_ | `'major' \| 'minor' \| 'patch'` | The version upgrade strategy (defaults to `minor`). |

Check out the [API reference](https://docs.coherent.global/spark-apis/impex-apis/import#request-body)
for more information.

```python
spark.impex.imp(
    destination={'source': 'my-folder/my-service', 'target': 'this-folder/my-service', 'upgrade': 'patch'},
    file=open('exported.zip', 'rb'),
    max_retries=7,
    retry_interval=3
)
```

### Returns

When successful, this method returns a JSON payload containing the import summary and
the imported entities that have been created/mapped in the destination tenant.
See the sample response below.

```json
{
  "object": "import",
  "id": "uuid",
  "response_timestamp": "1970-12-03T04:56:56.186Z",
  "status": "closed",
  "status_url": "https://excel.my-env.coherent.global/my-tenant/api/v4/import/job-uuid/status",
  "process_time": 123,
  "outputs": {
    "services": [
      {
        "service_uri_source": "my-folder/my-service",
        "folder_source": "my-folder",
        "service_source": "my-service",
        "folder_destination": "my-folder",
        "service_destination": "my-service",
        "service_uri_destination": "my-folder/my-service",
        "service_id_destination": "uuid",
        "status": "added"
      }
    ],
    "service_versions": [
      {
        "service_uri_source": "my-folder/my-service[0.1.0]",
        "folder_source": "my-folder",
        "service_source": "my-service",
        "version_source": "0.1.0",
        "version_id_source": "uuid",
        "folder_destination": "my-folder",
        "service_destination": "my-service",
        "version_destination": "0.1.0",
        "service_uri_destination": "my-folder/my-service[0.1.0]",
        "service_id_destination": "uuid",
        "version_id_destination": "uuid",
        "status": "added"
      },
      {
        "service_uri_source": "my-folder/my-service[0.2.0]",
        "folder_source": "my-folder",
        "service_source": "my-service",
        "version_source": "0.2.0",
        "version_id_source": "uuid",
        "folder_destination": "my-folder",
        "service_destination": "my-service",
        "version_destination": "0.2.0",
        "service_uri_destination": "my-folder/my-service[0.2.0]",
        "service_id_destination": "uuid",
        "version_id_destination": "uuid",
        "status": "added"
      }
    ]
  },
  "errors": null,
  "warnings": [],
  "source_system": "Spark Python SDK",
  "correlation_id": null
}
```

Being transactional, this method will create an import job, and poll its status
continuously until it completes the import process. You may consider using the
`imports` resource directly and control the import process manually:

- `Spark.impex.imports.initiate(data)` creates an import job.
- `Spark.impex.imports.get_status(job_id)` gets an import job's status.

Remember that exporting and importing entities is a time-consuming process. Be sure
to use enough retries and intervals to avoid timeouts.

[Back to top](#impex-api) or [Next: Other APIs](./misc.md)

<!-- References -->

[export-api]: https://docs.coherent.global/spark-apis/impex-apis/export
