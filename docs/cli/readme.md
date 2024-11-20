# Coherent Spark CLI

Coherent Spark CLI (currently in **beta**) is a command-line interface that lets
developers interact with the Coherent Spark platform. It is built on top of the
[SDK] and allows you to perform basic operations such as authenticating to Spark,
listing available services, and executing Spark services.

This CLI is designed for developers who want to interact with the platform in a
more programmatic way, without having to write code.

## Installation

To install the CLI, you can use the following command:

```bash
pip install 'cspark[cli]'
```

> **Python 3.8** or higher is required to install and run this CLI program.

## Usage

```bash
cspark --help
```

[![intro.png](intro.png)](intro.png)

As you can see, the CLI provides the following base commands:

- `init`: Initialize a new Spark configuration profile.
- `config`: Manage Coherent Spark configuration profiles.
- `auth`: Authenticate with Spark using OAuth2 client credentials.
- `services`: Manage Spark services.
- `versions`: Interact with versions of a Spark service.

For example, run the following command to execute a Spark service:

```bash
cspark services execute "my-folder/my-service" --inputs '{"value": 42}'
```

This command relies on the Spark settings and authentication of an active profile
to build the request and execute the service. Run `cspark config --help` to learn
how to manage your profiles.

[![flow.png](flow.png)](flow.png)

<!-- References -->
[sdk]:https://pypi.org/project/cspark/
