import sys

import click
from cspark.sdk import Client, SparkError


@click.group(name='services', help='Manage Spark services')
def services_cmd():
    pass


class ServicesListCommand(click.Command):
    def __init__(self):
        super().__init__(
            name='list',
            help='List available services',
            callback=self.get_versions,
            params=[
                click.Argument(['uri'], type=str),
                click.Option(
                    ['-b', '--base-url'],
                    type=str,
                    help='The base URL to use for the request',
                ),
                click.Option(
                    ['-T', '--tenant'],
                    type=str,
                    help='The tenant name',
                ),
                click.Option(
                    ['-e', '--env'],
                    type=str,
                    help='The environment to use for the request',
                ),
                click.Option(
                    ['-t', '--token'],
                    type=str,
                    help='The token to use for authentication',
                ),
            ],
        )

    def get_versions(self, uri: str, base_url: str, tenant: str, env: str, token: str):
        try:
            client = Client(base_url=base_url, env=env, tenant=tenant, token=token, logger=False)
            versions = client.services.get_versions(uri)
            click.echo(f'Versions for {uri}:\n{versions}')
            sys.exit(0)
        except SparkError as exc:
            click.echo(exc.message + (f'\n\n{exc.details}' if exc.details else ''), err=True)
            sys.exit(1)


services_cmd.add_command(ServicesListCommand())
