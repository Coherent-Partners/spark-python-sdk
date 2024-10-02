import json

import click
from cspark.sdk import Client, SparkError
from rich.console import Console

from .._utils import get_active_profile
from ._api import header_option, parse_headers


@click.group(name='versions', help='Interact with versions of a Spark service')
def versions_cmd():
    pass


@click.command(name='list', help='List available versions of a service')
@click.argument('uri', type=str, metavar='<URI>')
@header_option()
@click.option('--latest', is_flag=True, default=False, help='Show only the latest version')
def list_versions(uri: str, header: list[str], latest: bool) -> None:
    profile = get_active_profile()

    try:
        client = Client(**profile.to_config())
        client.config.extra_headers.update(parse_headers(header))  # type: ignore
        with client.services as s:
            versions = s.get_versions(uri)
            output = versions.data

        if latest and isinstance(output, (list, tuple)) and len(output) > 0:
            output = output[0]

        click.echo(json.dumps(output, indent=2))
    except SparkError as exc:
        Console().print(f'[red]✗[/red] {exc.message}')
        raise click.exceptions.Exit(1) from exc


versions_cmd.add_command(list_versions)
