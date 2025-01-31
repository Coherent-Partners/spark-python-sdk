import json

import click
from cspark.sdk import Client, SparkError
from rich.console import Console

from .._utils import get_active_profile
from ._api import AliasedGroup, header_option, parse_pairs


@click.group(
    name='versions',
    help='Interact with versions of a Spark service',
    options_metavar='',
    cls=AliasedGroup,
    aliases={'ls': 'list', 'get': 'list'},
)
def versions_cmd():
    pass


@versions_cmd.command(name='list', help='List available versions of a service')
@click.argument('uri', type=str, metavar='<SERVICE URI>')
@header_option()
@click.option('--latest', is_flag=True, default=False, help='Show only the latest version')
def list_versions(uri: str, headers: list[str], latest: bool) -> None:
    profile = get_active_profile()
    console = Console()

    try:
        client = Client(**profile.to_config())
        client.config.extra_headers.update(parse_pairs(headers))
        with client.services as s:
            versions = s.get_versions(uri).data

        if latest and isinstance(versions, (list, tuple)) and len(versions) > 0:
            versions = versions[0]

        click.echo(json.dumps(versions, indent=2))
    except SparkError as err:
        console.print(f'[red]✗[/red] {err.message}')
        raise click.exceptions.Exit(1) from err
    except Exception as exc:
        console.print(f'[red]✗[/red] {exc}')
        raise click.exceptions.Exit(1) from exc
