import json

import click
from cspark.sdk import Client, Config, SparkError
from rich.console import Console

from .._utils import get_active_profile
from ._api import Services, header_option, parse_headers


@click.group(name='services', help='Manage Spark services')
def services_cmd():
    pass


@click.command(name='list', help='List available services in a folder')
@click.argument('folder', type=str, metavar='<FOLDER NAME>')
@click.option('--name-only', is_flag=True, default=False, help='Show service names only')
@click.option('-d', '--data', type=str, metavar='<JSON>', help='Pagination data to send with the request')
@header_option()
def list_services(folder: str, name_only: bool, data: str, header: list[str]) -> None:
    profile = get_active_profile()
    console = Console()

    try:
        config = Config(**profile.to_config())
        config.extra_headers.update(parse_headers(header))  # type: ignore
        with Services(config) as s:
            response = s.get(folder, data).data

        output = response['data']  # type: ignore
        if name_only:
            output = [item['serviceName'] for item in output]  # type: ignore

        click.echo(json.dumps(output, indent=2))
    except SparkError as err:
        console.print(f'[red]✗[/red] {err.message}')
        raise click.exceptions.Exit(1) from err
    except Exception as exc:
        console.print(f'[red]✗[/red] {exc}')
        raise click.exceptions.Exit(1) from exc


@click.command(name='delete', help='Delete services in a folder (irreversible - use with caution)')
@click.option('-f', '--folder', type=str, metavar='<FOLDER NAME>', help='Name of the folder to delete services from')
@click.argument('names', type=str, metavar='<SERVICE NAMES>', nargs=-1)
@header_option()
def delete_services(folder: str, names: list[str], header: list[str]) -> None:
    profile = get_active_profile()
    console = Console()

    try:
        client = Client(**profile.to_config())
        client.config.extra_headers.update(parse_headers(header))  # type: ignore

        with client.services as s:
            for service in names:
                response = s.delete(folder=folder, service=service).data
                if response.get('status', '').lower() == 'success':  # type: ignore
                    click.echo(f'service deleted: {service}')

    except SparkError as err:
        console.print(f'[red]✗[/red] {err.message}')
        raise click.exceptions.Exit(1) from err
    except Exception as exc:
        console.print(f'[red]✗[/red] {exc}')
        raise click.exceptions.Exit(1) from exc


services_cmd.add_command(list_services)
services_cmd.add_command(delete_services)
