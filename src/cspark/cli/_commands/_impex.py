from __future__ import annotations

import pathlib
from typing import Any, Optional

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


class DefaultRunGroup(AliasedGroup):
    """Group that inserts a default `run` command when the first arg is not a subcommand."""

    def parse_args(self, ctx: click.Context, args: list[str]) -> list[str]:  # type: ignore[override]
        help_flags = {'--help', '-h'}
        if any(a in help_flags for a in args) and not (args and args[0] in self.commands):
            return super().parse_args(ctx, args)  # type: ignore[return-value]

        if args and not args[0].startswith('-'):
            if args[0] not in self.commands and args[0] not in self.aliases:
                args = ['run', *args]
        elif not args or (args and args[0].startswith('-')):
            # options-only invocation -> default to run
            if 'run' in self.commands:
                args = ['run', *args]
        return super().parse_args(ctx, args)  # type: ignore[return-value]


@click.group(name='export', help='Export Spark services', cls=DefaultRunGroup)
def export_cmd():
    pass


@export_cmd.command(name='run', help='Export services and download the resulting package')
@click.option('--folder', 'folders', type=str, multiple=True, metavar='<FOLDER>', help='Folders to export (repeatable)')
@click.option('--service', 'services', type=str, multiple=True, metavar='<URI>', help='Services to export (repeatable)')
@click.option('--version-id', 'version_ids', type=str, multiple=True, metavar='<ID>', help='Version IDs (repeatable)')
@click.option('--file-filter', type=str, metavar='<FILTER>', help='File filter (default: migrate)')
@click.option('--version-filter', type=str, metavar='<FILTER>', help='Version filter (default: latest)')
@click.option('--source-system', type=str, metavar='<NAME>', help='Source system metadata')
@click.option('--correlation-id', type=str, metavar='<ID>', help='Correlation ID')
@output_option()
@header_option()
def export_run(
    folders: tuple,
    services: tuple,
    version_ids: tuple,
    file_filter: Optional[str],
    version_filter: Optional[str],
    source_system: Optional[str],
    correlation_id: Optional[str],
    output: Optional[pathlib.Path],
    headers: list[str],
) -> None:
    profile = get_active_profile()
    console = Console(stderr=True)

    if not folders and not services and not version_ids:
        raise click.BadParameter('provide at least one of --folder, --service, or --version-id')

    try:
        with Client(**profile.to_config()) as client:
            client.config.extra_headers.update(parse_pairs(headers))
            with spinner('Exporting...'):
                downloads = client.impex.exp(
                    folders=list(folders) if folders else None,
                    services=list(services) if services else None,
                    version_ids=list(version_ids) if version_ids else None,
                    file_filter=file_filter,
                    version_filter=version_filter,
                    source_system=source_system or 'Coherent Spark CLI',
                    correlation_id=correlation_id,
                )

        if not downloads:
            raise SparkError.sdk('export completed but no files were downloaded')

        for idx, response in enumerate(downloads):
            if output and len(downloads) > 1:
                target: Optional[pathlib.Path] = output.parent / f'{output.stem}_{idx + 1}{output.suffix}'
            else:
                target = output
            default = 'export.zip' if len(downloads) == 1 else f'export_{idx + 1}.zip'
            path = write_response_file(response, target, default_name=default)
            console.print(f'[green]✓[/green] wrote {path}')
    except SparkError as err:
        handle_error(err)
    except Exception as exc:
        handle_error(exc)


@export_cmd.command(name='describe', help='Describe export jobs across the tenant')
@header_option()
def export_describe(headers: list[str]) -> None:
    profile = get_active_profile()

    try:
        with Client(**profile.to_config()) as client:
            client.config.extra_headers.update(parse_pairs(headers))
            response = client.impex.exports.describe()
        echo_json(response.data)
    except SparkError as err:
        handle_error(err)
    except Exception as exc:
        handle_error(exc)


@export_cmd.command(name='status', help='Get the status of an export job')
@click.argument('job_id', type=str, metavar='<JOB ID>')
@header_option()
def export_status(job_id: str, headers: list[str]) -> None:
    profile = get_active_profile()

    try:
        with Client(**profile.to_config()) as client:
            client.config.extra_headers.update(parse_pairs(headers))
            with spinner(f'Checking export job {job_id}...'):
                response = client.impex.exports.get_status(job_id=job_id)
        echo_json(response.data)
    except SparkError as err:
        handle_error(err)
    except Exception as exc:
        handle_error(exc)


@export_cmd.command(name='cancel', help='Cancel an export job')
@click.argument('job_id', type=str, metavar='<JOB ID>')
@header_option()
def export_cancel(job_id: str, headers: list[str]) -> None:
    profile = get_active_profile()

    try:
        with Client(**profile.to_config()) as client:
            client.config.extra_headers.update(parse_pairs(headers))
            response = client.impex.exports.cancel(job_id)
        echo_json(response.data)
    except SparkError as err:
        handle_error(err)
    except Exception as exc:
        handle_error(exc)


@click.group(name='import', help='Import Spark services', cls=DefaultRunGroup)
def import_cmd():
    pass


@import_cmd.command(name='run', help='Import a package into Spark')
@click.argument(
    'file_path',
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=pathlib.Path),
    metavar='<PACKAGE FILE>',
)
@click.option(
    '-d',
    '--destination',
    required=True,
    type=str,
    multiple=True,
    metavar='<URI>',
    help='Destination service URI(s). Repeatable. Use source=target for remapping.',
)
@click.option(
    '--if-present',
    type=click.Choice(['add_version', 'replace', 'skip'], case_sensitive=False),
    help='Behavior when the service already exists',
)
@click.option('--source-system', type=str, metavar='<NAME>', help='Source system metadata')
@click.option('--correlation-id', type=str, metavar='<ID>', help='Correlation ID')
@header_option()
def import_run(
    file_path: pathlib.Path,
    destination: tuple,
    if_present: Optional[str],
    source_system: Optional[str],
    correlation_id: Optional[str],
    headers: list[str],
) -> None:
    profile = get_active_profile()
    console = Console(stderr=True)

    destinations: list[Any] = []
    for dest in destination:
        if '=' in dest:
            source, target = dest.split('=', 1)
            destinations.append({'source': source, 'target': target})
        else:
            destinations.append(dest)

    try:
        with Client(**profile.to_config()) as client:
            client.config.extra_headers.update(parse_pairs(headers))
            with file_path.open('rb') as file:
                with spinner(f'Importing {file_path.name}...'):
                    status = client.impex.imp(
                        destinations if len(destinations) > 1 else destinations[0],
                        file,
                        if_present=if_present,
                        source_system=source_system or 'Coherent Spark CLI',
                        correlation_id=correlation_id,
                    )
        console.print('[green]✓[/green] Import completed')
        echo_json(status.data)
    except SparkError as err:
        handle_error(err)
    except Exception as exc:
        handle_error(exc)


@import_cmd.command(name='describe', help='Describe import jobs across the tenant')
@header_option()
def import_describe(headers: list[str]) -> None:
    profile = get_active_profile()

    try:
        with Client(**profile.to_config()) as client:
            client.config.extra_headers.update(parse_pairs(headers))
            response = client.impex.imports.describe()
        echo_json(response.data)
    except SparkError as err:
        handle_error(err)
    except Exception as exc:
        handle_error(exc)


@import_cmd.command(name='status', help='Get the status of an import job')
@click.argument('job_id', type=str, metavar='<JOB ID>')
@header_option()
def import_status(job_id: str, headers: list[str]) -> None:
    profile = get_active_profile()

    try:
        with Client(**profile.to_config()) as client:
            client.config.extra_headers.update(parse_pairs(headers))
            with spinner(f'Checking import job {job_id}...'):
                response = client.impex.imports.get_status(job_id=job_id)
        echo_json(response.data)
    except SparkError as err:
        handle_error(err)
    except Exception as exc:
        handle_error(exc)
