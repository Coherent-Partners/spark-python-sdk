## Promote Spark Services from Lower to Higher Environments

Moving Spark services across different environments doesn't follow the same conventional
deployment practices as other software applications. Spark provides a series of APIs
known as [ImpEx (Import/Export) API][impex-apis] to facilitate the migration of services
from one tenant to another.

This use case demonstrates how to programmatically move Spark services across tenants
or environments.

## Running the Example

To run this use case, replace the placeholder values with your own in [main.py](main.py):

- `FROM_SPARK_SETTINGS`: Spark settings of the source tenant.
- `FROM_BEARER_TOKEN`: Bearer token of the source tenant.
- `TO_SPARK_SETTINGS`: Spark settings of the target tenant.
- `TO_OAUTH_CREDS`: OAuth2 credentials for the target tenant.

Then, run the following command:

```bash
poetry run python main.py
```

Do note that Spark settings in this case are expected as a stringified object compliant
with the SDK client configuration. For example, the settings for the source tenant
`FROM_SPARK_SETTINGS` are defined as follows:

```json
{
  "env": "my-env",
  "tenant": "my-tenant",
  "timeout": 90000,
  "max_retries": 10,
  "retry_interval": 3,
  "services": ["folder-name/service-name"]
}
```

Visit [Authentication](../../../docs/authentication.md) to learn more about the
different authorization methods.

This execution consists of two routines: `exp()` and `imp()`.

- `exp()` is responsible for exporting Spark services from the source
  tenant. It triggers the export operation using the [Export API][export-api],
  polls its status until completion, and downloads the exported entities.
  A copy of the exported entities is saved to disk for future reference.

- `imp()` is run automatically once `exp()` is done. It uses the exported entities
  (i.e., binary file) returned by `exp()` and imports them into the target tenant.

See an example of the expected logs below:

[![outputs.png](outputs.png)](outputs.png)

## What's Next

You may choose to implement this use case in a CI/CD pipeline of your choice (Circle CI,
Jenkins, Azure DevOps, etc.) to automate your deployment process. This can be achieved
by integrating the workflow with a CI/CD tool that harnesses ImpEx API.

For instance, [workflow.yml](workflow.yml) is an example of how to integrate
this use case into [GitHub Actions][gha-intro]. It relies on [impex.py](impex.py)
and expects the appropriate environment variables to be set in the repository.

As the workflow runs, it will trigger the `impex.py` script, which in turn expects the
following positional arguments:

```bash
poetry run python impex.py "$FROM_SETTINGS" "$BEARER_TOKEN" "$TO_SETTINGS" "$TO_OAUTH"
```

> [!NOTE]
> The `impex.py` script is an extension of `main.py` designed simply to accommodate
> the environment variables set in the repository.
> You might modify both the script and workflow to suit your needs.

<!-- References -->

[impex-apis]: https://docs.coherent.global/api-details/impex-apis
[export-api]: https://docs.coherent.global/spark-apis/impex-apis/export
[gha-intro]: https://docs.github.com/en/actions/about-github-actions/understanding-github-actions
