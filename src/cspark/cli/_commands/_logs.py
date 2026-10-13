from __future__ import annotations

import pathlib
from typing import Optional

import click
from cspark.sdk import Client, SparkError
from rich.console import Console

from .._utils import get_active_profile
from ._api import (
    AliasedGroup,
    echo_json,
    handle_error,
    header_option,
    output_option,
    parse_pairs,
    spinner,
    write_response_file,
)


@click.group(
    name='logs',
    help='Inspect Spark execution history and download logs',
    options_metavar='',
    cls=AliasedGroup,
    aliases={'get': 'get', 'dl': 'download'},
)
def logs_cmd():
    pass


@logs_cmd.command(name='get', help='Get execution history by call ID')
@click.argument('call_id', type=str, metavar='<CALL ID>')
@header_option()
def get_log(call_id: str, headers: list[str]) -> None:
    profile = get_active_profile()

    try:
        with Client(**profile.to_config()) as client:
            client.config.extra_headers.update(parse_pairs(headers))
            response = client.logs.get(call_id)
        echo_json(response.data)
    except SparkError as err:
        handle_error(err)
    except Exception as exc:
        handle_error(exc)


@logs_cmd.command(name='download', help='Download execution logs for a service')
@click.option('-f', '--folder', required=True, type=str, metavar='<FOLDER>', help='Folder name')
@click.option('-s', '--service', required=True, type=str, metavar='<SERVICE>', help='Service name')
@click.option(
    '--type', 'log_type', type=click.Choice(['json', 'csv'], case_sensitive=False), default='json', show_default=True
)
@click.option('--version-id', type=str, metavar='<ID>', help='Filter by version ID')
@click.option(
    '--call-id', 'call_ids', type=str, multiple=True, metavar='<CALL ID>', help='Call IDs to include (repeatable)'
)
@click.option('--start-date', type=str, metavar='<DATE>', help='Start date filter')
@click.option('--end-date', type=str, metavar='<DATE>', help='End date filter')
@click.option('--source-system', type=str, metavar='<NAME>', help='Source system filter')
@click.option('--correlation-id', type=str, metavar='<ID>', help='Correlation ID filter')
@click.option('--timezone-offset', type=str, metavar='<OFFSET>', help='Timezone offset')
@output_option()
@header_option()
def download_logs(
    folder: str,
    service: str,
    log_type: str,
    version_id: Optional[str],
    call_ids: tuple,
    start_date: Optional[str],
    end_date: Optional[str],
    source_system: Optional[str],
    correlation_id: Optional[str],
    timezone_offset: Optional[str],
    output: Optional[pathlib.Path],
    headers: list[str],
) -> None:
    profile = get_active_profile()
    console = Console(stderr=True)

    try:
        with Client(**profile.to_config()) as client:
            client.config.extra_headers.update(parse_pairs(headers))
            with spinner(f'Downloading {log_type} logs...'):
                response = client.logs.download(
                    folder=folder,
                    service=service,
                    type=log_type,
                    version_id=version_id,
                    call_ids=list(call_ids) if call_ids else None,
                    start_date=start_date,
                    end_date=end_date,
                    source_system=source_system,
                    correlation_id=correlation_id,
                    timezone_offset=timezone_offset,
                )

        if output:
            path = write_response_file(response, output, default_name=f'{folder}_{service}_logs.{log_type}')
            console.print(f'[green]✓[/green] wrote {path}')
        else:
            # Prefer downloaded log content when available; otherwise show job metadata.
            if getattr(response, 'buffer', None):
                try:
                    click.echo(response.buffer.decode('utf-8'))
                except Exception:
                    echo_json(response.data)
            else:
                echo_json(response.data)
    except SparkError as err:
        handle_error(err)
    except Exception as exc:
        handle_error(exc)


@logs_cmd.command(name='rehydrate', help='Rehydrate an execution into a downloadable workbook')
@click.argument('uri', type=str, metavar='<SERVICE URI>')
@click.option('--call-id', required=True, type=str, metavar='<CALL ID>', help='Execution call ID')
@click.option('--index', type=int, metavar='<N>', help='Batch row index (when applicable)')
@click.option('--legacy', is_flag=True, default=False, help='Use the legacy download endpoint')
@output_option()
@header_option()
def rehydrate_log(
    uri: str,
    call_id: str,
    index: Optional[int],
    legacy: bool,
    output: Optional[pathlib.Path],
    headers: list[str],
) -> None:
    profile = get_active_profile()

    try:
        with Client(**profile.to_config()) as client:
            client.config.extra_headers.update(parse_pairs(headers))
            with spinner('Rehydrating execution...'):
                response = client.logs.rehydrate(uri, call_id=call_id, index=index, legacy=legacy)

        path = write_response_file(response, output, default_name=f'rehydrate_{call_id}.xlsx')
        click.echo(f'wrote {path}')
    except SparkError as err:
        handle_error(err)
    except Exception as exc:
        handle_error(exc)
