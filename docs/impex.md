<!-- markdownlint-disable-file MD024 -->

# ImpEx API

| Verb                       | Description                                                                       |
| -------------------------- | --------------------------------------------------------------------------------- |
| `Spark.impex.export(data)` | [Export Spark entities (versions, services, or folders)](#export-spark-entities). |

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
| _version\_ids_      | `None \| list[str]`     | 1+ version UUID(s) of the desired service.                         |
| _file\_filter_    | `migrate \| onpremises` | For data migration or hybrid deployments (defaults to `migrate`).  |
| _version\_filter_ | `latest \| all`         | Which version of the file to export (defaults to `latest`).        |
| _source\_system_  | `None \| str`           | Source system name to export from (e.g., `Spark Python SDK`).      |
| _correlation\_id_ | `None \| str`           | Correlation ID for the export (useful for tagging).                |
| _max\_retries_    | `None \| int`           | Maximum number of retries when checking the export status.         |
| _retry\_interval_ | `None \| float`         | Interval between status check retries in seconds.                  |

> [!NOTE]
> Remember that a service URI can be one of the following:
>
> - `{folder}/{service}[?{version}]` or
> - `service/{serviceId}` or
> - `version/{versionId}`.

Check out the [API reference](https://docs.coherent.global/spark-apis/impex-apis/export#request-body)
for more information.

```python
spark.impex.export(
  services=['my-folder/my-service[0.4.2]', 'my-other-folder/my-service-2'],
  file_filter='onpremises',
  max_retries=5,
  retry_interval=3,
)
```

### Returns

When successful, this method returns an array of exported entities, where each entity
is an `HttpResponse` object with the buffer containing the exported entity.

### Non-Transactional Methods

This method is transactional. It will initiate an export job, poll its status
until it completes, and download the exported files. If you need more control over
these steps, consider using the `exports` resource directly. You may use the following
methods:

- `Spark.impex.exports.initiate(data)` creates an export job.
- `Spark.impex.exports.get_status(job_id)` gets an export job's status.
- `Spark.impex.exports.download(urls)` downloads the exported files as a ZIP.

[Back to top](#impex-api) or [Next: Other APIs](./misc.md)

<!-- References -->

[export-api]: https://docs.coherent.global/spark-apis/impex-apis/export
