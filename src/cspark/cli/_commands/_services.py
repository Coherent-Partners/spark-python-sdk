import json

import click
from cspark.sdk import Client, Config, SparkError
from rich.console import Console

from .._utils import get_active_profile
from ._api import AliasedGroup, Services, header_option, json_parse, params_option, parse_pairs


@click.group(
    name='services',
    help='Manage Spark services',
    options_metavar='',
    cls=AliasedGroup,
    aliases={'ls': 'list', 'exec': 'execute', 'run': 'execute', 'find': 'search', 'del': 'delete'},
)
def services_cmd():
    pass


@services_cmd.command(name='list', help='List available services in a folder')
@click.argument('folder', type=str, metavar='<FOLDER NAME>')
@click.option('--name-only', is_flag=True, default=False, help='Show service names only')
@click.option('-d', '--data', type=str, metavar='<JSON>', help='Pagination data to send with the request')
@header_option()
def list_services(folder: str, name_only: bool, data: str, headers: list[str]) -> None:
    profile = get_active_profile()
    console = Console()

    try:
        config = Config(**profile.to_config())
        config.extra_headers.update(parse_pairs(headers))
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


@services_cmd.command(name='search', help='Search available services')
@click.option('-d', '--data', type=str, metavar='<JSON>', help='Pagination data to send with the request')
@header_option()
@click.option('--show-all', is_flag=True, default=False, help='Show the complete response data')
def search_services(data: str, headers: list[str], show_all: bool) -> None:
    profile = get_active_profile()
    console = Console()

    try:
        client = Client(**profile.to_config())
        client.config.extra_headers.update(parse_pairs(headers))
        with client.services as s:
            response = s.search(**json_parse(data))

        output = response.data
        if not show_all:
            output = output.get('response_data', {})  # type: ignore

        click.echo(json.dumps(output, indent=2))
    except SparkError as err:
        console.print(f'[red]✗[/red] {err.message}')
        raise click.exceptions.Exit(1) from err
    except Exception as exc:
        console.print(f'[red]✗[/red] {exc}')
        raise click.exceptions.Exit(1) from exc


@services_cmd.command(name='execute', help='Execute Spark services')
@click.argument('uri', type=str, metavar='<SERVICE URI>')
@click.option('-i', '--inputs', type=str, metavar='<JSON>', help='Input data to send with the request')
@params_option()
@header_option()
@click.option('--show-all', is_flag=True, default=False, help='Show the complete response data')
def execute_services(uri: str, inputs: str, params: list[str], headers: list[str], show_all: bool) -> None:
    profile = get_active_profile()
    console = Console()

    try:
        client = Client(**profile.to_config())
        client.config.extra_headers.update(parse_pairs(headers))
        with client.services as s:
            metadata = parse_pairs(params, infer_type=True)
            outputs = s.execute(uri, inputs=inputs, source_system='Coherent Spark CLI', **metadata).data

        if not show_all:
            outputs = outputs.get('outputs') or outputs.get('response_data', {}).get('outputs')  # type: ignore

        click.echo(json.dumps(outputs, indent=2))
    except SparkError as err:
        console.print(f'[red]✗[/red] {err.message}')
        raise click.exceptions.Exit(1) from err
    except Exception as exc:
        console.print(f'[red]✗[/red] {exc}')
        raise click.exceptions.Exit(1) from exc


@services_cmd.command(name='delete', help='Delete services in a folder (irreversible - use with caution)')
@click.option('-f', '--folder', type=str, metavar='<FOLDER NAME>', help='Name of the folder to delete services from')
@click.argument('names', type=str, metavar='<SERVICE NAMES>', nargs=-1)
@header_option()
def delete_services(folder: str, names: list[str], headers: list[str]) -> None:
    profile = get_active_profile()
    console = Console()

    if not names:
        raise click.BadParameter('at least one service name must be provided.')

    try:
        client = Client(**profile.to_config())
        client.config.extra_headers.update(parse_pairs(headers))

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
