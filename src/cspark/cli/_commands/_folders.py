import json

import click
from cspark.sdk import Client, SparkError
from InquirerPy import inquirer
from rich.console import Console

from .._utils import get_active_profile
from ._api import AliasedGroup, header_option, json_parse, parse_pairs


@click.group(
    name='folders',
    help='Manage Spark folders',
    options_metavar='',
    cls=AliasedGroup,
    aliases={'ls': 'list', 'del': 'delete'},
)
def folders_cmd():
    pass


@folders_cmd.command(name='list', help='List available folders')
@click.option('--name-only', is_flag=True, default=False, help='Show folder names only')
@click.option('-d', '--data', type=str, metavar='<JSON>', help='Pagination data to send with the request')
@header_option()
def list_folders(name_only: bool, data: str, headers: list[str]) -> None:
    profile = get_active_profile()
    console = Console()

    try:
        client = Client(**profile.to_config())
        client.config.extra_headers.update(parse_pairs(headers))
        with client.folders as f:
            response = f.find(**json_parse(data)).data

        output = response['data']  # type: ignore
        if name_only:
            output = [item['name'] for item in output]  # type: ignore

        click.echo(json.dumps(output, indent=2))
    except SparkError as err:
        console.print(f'[red]✗[/red] {err.message}')
        raise click.exceptions.Exit(1) from err
    except Exception as exc:
        console.print(f'[red]✗[/red] {exc}')
        raise click.exceptions.Exit(1) from exc


@folders_cmd.command(name='delete', help='Delete a folder (and all its services)')
@click.argument('names', type=str, metavar='<FOLDER NAMES>', nargs=-1)
@header_option()
def delete_services(names: list[str], headers: list[str]) -> None:
    profile = get_active_profile()
    console = Console()

    if not names:
        raise click.BadParameter('at least one folder name must be provided.')

    try:
        client = Client(**profile.to_config())
        client.config.extra_headers.update(parse_pairs(headers))
        with client.folders as f:
            for folder in names:
                confirmed = inquirer.confirm(  # type: ignore
                    message=f'Are you sure you want to delete "{folder}" and all its services?', default=False
                ).execute()
                if not confirmed:
                    click.echo(f'folder skipped: {folder}')
                    continue

                response = f.delete(folder).data
                if response.get('status', '').lower() == 'success':  # type: ignore
                    click.echo(f'folder deleted: {folder}')

    except SparkError as err:
        console.print(f'[red]✗[/red] {err.message}')
        raise click.exceptions.Exit(1) from err
    except Exception as exc:
        console.print(f'[red]✗[/red] {exc}')
        raise click.exceptions.Exit(1) from exc
