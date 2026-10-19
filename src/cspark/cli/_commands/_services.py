from __future__ import annotations

import pathlib
import time
from typing import Optional

import click
from cspark.sdk import Client, SparkError, Uri
from rich.console import Console

from .._utils import get_active_profile
from ._api import (
    AliasedGroup,
    echo_json,
    handle_error,
    header_option,
    json_parse,
    output_option,
    params_option,
    parse_pairs,
    progress_status,
    spinner,
    write_response_file,
)


@click.group(
    name='services',
    help='Manage Spark services',
    options_metavar='',
    cls=AliasedGroup,
    aliases={
        'ls': 'list',
        'exec': 'execute',
        'run': 'execute',
        'find': 'search',
        'del': 'delete',
    },
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

    try:
        with Client(**profile.to_config()) as client:
            client.config.extra_headers.update(parse_pairs(headers))
            endpoint = f'product/{folder}/engines'
            url = Uri.of(base_url=client.config.base_url.value, version='api/v1', endpoint=endpoint)
            body = {'page': 1, 'pageSize': 100, 'search': [], 'sort': 'name1'}
            if data:
                body.update(json_parse(data))
            response = client.services.request(url, method='POST', body=body).data

        output = response['data']  # type: ignore
        if name_only:
            output = [item['serviceName'] for item in output]  # type: ignore

        echo_json(output)
    except SparkError as err:
        handle_error(err)
    except Exception as exc:
        handle_error(exc)


@services_cmd.command(name='search', help='Search available services')
@click.option('-d', '--data', type=str, metavar='<JSON>', help='Pagination data to send with the request')
@header_option()
@click.option('--show-all', is_flag=True, default=False, help='Show the complete response data')
def search_services(data: str, headers: list[str], show_all: bool) -> None:
    profile = get_active_profile()

    try:
        with Client(**profile.to_config()) as client:
            client.config.extra_headers.update(parse_pairs(headers))
            response = client.services.search(**json_parse(data))

        output = response.data
        if not show_all:
            output = output.get('response_data', {})  # type: ignore

        echo_json(output)
    except SparkError as err:
        handle_error(err)
    except Exception as exc:
        handle_error(exc)


@services_cmd.command(name='execute', help='Execute Spark services')
@click.argument('uri', type=str, metavar='<SERVICE URI>')
@click.option('-i', '--inputs', type=str, metavar='<JSON>', help='Input data to send with the request')
@params_option()
@header_option()
@click.option('--show-all', is_flag=True, default=False, help='Show the complete response data')
def execute_services(uri: str, inputs: str, params: list[str], headers: list[str], show_all: bool) -> None:
    profile = get_active_profile()

    try:
        with Client(**profile.to_config()) as client:
            client.config.extra_headers.update(parse_pairs(headers))
            metadata = parse_pairs(params, infer_type=True)
            outputs = client.services.execute(uri, inputs=inputs, source_system='Coherent Spark CLI', **metadata).data

        if not show_all:
            outputs = outputs.get('outputs') or outputs.get('response_data', {}).get('outputs')  # type: ignore

        echo_json(outputs)
    except SparkError as err:
        handle_error(err)
    except Exception as exc:
        handle_error(exc)


@services_cmd.command(name='create', help='Create a service (upload, compile, and publish)')
@click.argument('name', type=str, metavar='<SERVICE NAME>')
@click.option('-f', '--folder', required=True, type=str, metavar='<FOLDER>', help='Folder to create the service in')
@click.option(
    '--file',
    'file_path',
    required=True,
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=pathlib.Path),
    metavar='<FILE>',
    help='Path to the Excel service file',
)
@click.option('--draft-name', type=str, metavar='<NAME>', help='Draft service name')
@click.option('--versioning', type=click.Choice(['major', 'minor', 'patch'], case_sensitive=False), help='Version bump')
@click.option('--label', type=str, metavar='<LABEL>', help='Version label')
@click.option('--release-notes', type=str, metavar='<TEXT>', help='Release notes')
@click.option('--tags', type=str, multiple=True, metavar='<TAG>', help='Tags to attach (repeatable)')
@click.option('--start-date', type=str, metavar='<DATE>', help='Effective start date')
@click.option('--end-date', type=str, metavar='<DATE>', help='Effective end date')
@click.option('--track-user', is_flag=True, default=False, help='Track user actions')
@header_option()
def create_service(
    name: str,
    folder: str,
    file_path: pathlib.Path,
    draft_name: Optional[str],
    versioning: Optional[str],
    label: Optional[str],
    release_notes: Optional[str],
    tags: tuple,
    start_date: Optional[str],
    end_date: Optional[str],
    track_user: bool,
    headers: list[str],
) -> None:
    profile = get_active_profile()
    console = Console(stderr=True)

    try:
        with Client(**profile.to_config()) as client:
            client.config.extra_headers.update(parse_pairs(headers))
            services = client.services
            compilation = services.compilation

            with file_path.open('rb') as file:
                with spinner(f'Uploading {file_path.name}...'):
                    upload = compilation.initiate(
                        folder=folder,
                        service=name,
                        file=file,
                        file_name=file_path.name,
                        versioning=versioning,
                        start_date=start_date,
                        end_date=end_date,
                    )

            job_id = ''
            if isinstance(upload.data, dict):
                job_id = upload.data.get('response_data', {}).get('nodegen_compilation_jobid') or ''

            if not job_id:
                raise SparkError.sdk('failed to start compilation job', upload.data)

            max_retries = client.config.max_retries
            retry_interval = client.config.retry_interval
            status_data = None

            with progress_status('Compiling... 0%') as update:
                retries = 0
                while retries <= max_retries:
                    status = compilation.get_status(
                        folder=folder,
                        service=name,
                        job_id=job_id,
                        max_retries=1,
                        retry_interval=retry_interval,
                        throwable=False,
                    )
                    response_data = isinstance(status.data, dict) and status.data.get('response_data', {}) or {}
                    progress = response_data.get('progress', 0)
                    status_name = response_data.get('status')
                    update(f'Compiling... {progress}%')

                    if progress == 100 and status_name == 'Success':
                        status_data = status.data
                        break

                    if progress >= 100:
                        status_data = status.data
                        break

                    retries += 1
                    if retries > max_retries:
                        raise SparkError.sdk(
                            f'compilation job status check timed out after {retries} attempts',
                            status.data,
                        )
                    time.sleep(retry_interval or 1.0)

            upload_data = upload.data.get('response_data', {}) if isinstance(upload.data, dict) else {}
            file_id = upload_data.get('original_file_documentid') or ''
            engine_id = upload_data.get('engine_file_documentid') or ''
            if not file_id or not engine_id:
                raise SparkError.sdk('compilation succeeded but upload document IDs are missing', upload.data)

            with spinner('Publishing service...'):
                published = services.publish(
                    folder=folder,
                    service=name,
                    file_id=file_id,
                    engine_id=engine_id,
                    draft_name=draft_name,
                    versioning=versioning,
                    start_date=start_date,
                    end_date=end_date,
                    track_user=track_user,
                    label=label,
                    release_notes=release_notes,
                    tags=list(tags) if tags else None,
                )

            console.print(f'[green]✓[/green] Service [cyan]{folder}/{name}[/cyan] created')
            echo_json({'upload': upload.data, 'compilation': status_data, 'publication': published.data})
    except SparkError as err:
        handle_error(err)
    except Exception as exc:
        handle_error(exc)


@services_cmd.command(name='schema', help='Get the schema of a Spark service')
@click.argument('uri', type=str, metavar='<SERVICE URI>')
@header_option()
def service_schema(uri: str, headers: list[str]) -> None:
    profile = get_active_profile()

    try:
        with Client(**profile.to_config()) as client:
            client.config.extra_headers.update(parse_pairs(headers))
            response = client.services.get_schema(uri)
        echo_json(response.data)
    except SparkError as err:
        handle_error(err)
    except Exception as exc:
        handle_error(exc)


@services_cmd.command(name='metadata', help='Get metadata for a Spark service')
@click.argument('uri', type=str, metavar='<SERVICE URI>')
@header_option()
def service_metadata(uri: str, headers: list[str]) -> None:
    profile = get_active_profile()

    try:
        with Client(**profile.to_config()) as client:
            client.config.extra_headers.update(parse_pairs(headers))
            response = client.services.get_metadata(uri)
        echo_json(response.data)
    except SparkError as err:
        handle_error(err)
    except Exception as exc:
        handle_error(exc)


@services_cmd.command(name='swagger', help='Get the Swagger definition of a Spark service')
@click.argument('uri', type=str, metavar='<SERVICE URI>')
@click.option('--version-id', type=str, metavar='<ID>', help='Specific version ID')
@click.option('--downloadable', is_flag=True, default=False, help='Request a downloadable Swagger file')
@click.option('--subservice', type=str, default='All', show_default=True, help='Subservice name')
@output_option()
@header_option()
def service_swagger(
    uri: str,
    version_id: Optional[str],
    downloadable: bool,
    subservice: str,
    output: Optional[pathlib.Path],
    headers: list[str],
) -> None:
    profile = get_active_profile()

    try:
        with Client(**profile.to_config()) as client:
            client.config.extra_headers.update(parse_pairs(headers))
            response = client.services.get_swagger(
                uri,
                version_id=version_id,
                downloadable=downloadable,
                subservice=subservice,
            )

        if output or downloadable:
            path = write_response_file(response, output, default_name='swagger.json')
            click.echo(f'wrote {path}')
        else:
            echo_json(response.data)
    except SparkError as err:
        handle_error(err)
    except Exception as exc:
        handle_error(exc)


@services_cmd.command(name='download', help='Download a Spark service file')
@click.argument('uri', type=str, metavar='<SERVICE URI>')
@click.option('--version-id', type=str, metavar='<ID>', help='Specific version ID')
@click.option(
    '--type', 'file_type', type=click.Choice(['original', 'configured'], case_sensitive=False), help='File type'
)
@click.option('--file-name', type=str, metavar='<NAME>', help='Remote file name hint')
@output_option()
@header_option()
def download_service(
    uri: str,
    version_id: Optional[str],
    file_type: Optional[str],
    file_name: Optional[str],
    output: Optional[pathlib.Path],
    headers: list[str],
) -> None:
    profile = get_active_profile()

    try:
        with Client(**profile.to_config()) as client:
            client.config.extra_headers.update(parse_pairs(headers))
            response = client.services.download(
                uri,
                version_id=version_id,
                file_name=file_name,
                type=file_type,
            )
        default = file_name or f'{uri.replace("/", "_")}.xlsx'
        path = write_response_file(response, output, default_name=default)
        click.echo(f'wrote {path}')
    except SparkError as err:
        handle_error(err)
    except Exception as exc:
        handle_error(exc)


@services_cmd.command(name='recompile', help='Recompile an existing Spark service version')
@click.argument('uri', type=str, metavar='<SERVICE URI>')
@click.option('--version-id', type=str, metavar='<ID>', help='Version ID to recompile')
@click.option('--compiler', type=str, metavar='<VERSION>', help='Compiler version (default: StableLatest)')
@click.option('--upgrade', type=click.Choice(['major', 'minor', 'patch'], case_sensitive=False), help='Version bump')
@click.option('--label', type=str, metavar='<LABEL>', help='Version label')
@click.option('--release-notes', type=str, metavar='<TEXT>', help='Release notes')
@click.option('--tags', type=str, multiple=True, metavar='<TAG>', help='Tags to attach (repeatable)')
@click.option('--start-date', type=str, metavar='<DATE>', help='Effective start date')
@click.option('--end-date', type=str, metavar='<DATE>', help='Effective end date')
@header_option()
def recompile_service(
    uri: str,
    version_id: Optional[str],
    compiler: Optional[str],
    upgrade: Optional[str],
    label: Optional[str],
    release_notes: Optional[str],
    tags: tuple,
    start_date: Optional[str],
    end_date: Optional[str],
    headers: list[str],
) -> None:
    profile = get_active_profile()

    try:
        with Client(**profile.to_config()) as client:
            client.config.extra_headers.update(parse_pairs(headers))
            with spinner('Recompiling service...'):
                response = client.services.recompile(
                    uri,
                    version_id=version_id,
                    compiler=compiler,
                    upgrade=upgrade,
                    label=label,
                    release_notes=release_notes,
                    tags=list(tags) if tags else None,
                    start_date=start_date,
                    end_date=end_date,
                )
        echo_json(response.data)
    except SparkError as err:
        handle_error(err)
    except Exception as exc:
        handle_error(exc)


@services_cmd.command(name='validate', help='Validate inputs against a Spark service')
@click.argument('uri', type=str, metavar='<SERVICE URI>')
@click.option('-i', '--inputs', type=str, metavar='<JSON>', help='Input data to validate')
@click.option(
    '--validation-type',
    type=click.Choice(['dynamic', 'static'], case_sensitive=False),
    help='Validation type',
)
@params_option()
@header_option()
def validate_service(
    uri: str,
    inputs: str,
    validation_type: Optional[str],
    params: list[str],
    headers: list[str],
) -> None:
    profile = get_active_profile()

    try:
        with Client(**profile.to_config()) as client:
            client.config.extra_headers.update(parse_pairs(headers))
            metadata = parse_pairs(params, infer_type=True)
            response = client.services.validate(
                uri,
                inputs=inputs,
                validation_type=validation_type,
                source_system='Coherent Spark CLI',
                **metadata,
            )
        echo_json(response.data)
    except SparkError as err:
        handle_error(err)
    except Exception as exc:
        handle_error(exc)


@services_cmd.command(name='exists', help='Check whether a service exists')
@click.argument('uri', type=str, metavar='<SERVICE URI>')
@header_option()
def service_exists(uri: str, headers: list[str]) -> None:
    profile = get_active_profile()

    try:
        with Client(**profile.to_config()) as client:
            client.config.extra_headers.update(parse_pairs(headers))
            exists = client.services.exists(uri)
        click.echo('true' if exists else 'false')
        if not exists:
            raise click.exceptions.Exit(1)
    except SparkError as err:
        handle_error(err)
    except click.exceptions.Exit:
        raise
    except Exception as exc:
        handle_error(exc)


@services_cmd.command(name='version', help='List available versions of a service')
@click.argument('uri', type=str, metavar='<SERVICE URI>')
@header_option()
@click.option('--latest', is_flag=True, default=False, help='Show only the latest version')
def service_version(uri: str, headers: list[str], latest: bool) -> None:
    profile = get_active_profile()

    try:
        with Client(**profile.to_config()) as client:
            client.config.extra_headers.update(parse_pairs(headers))
            versions = client.services.get_versions(uri).data

        if latest and isinstance(versions, (list, tuple)) and len(versions) > 0:
            versions = versions[0]

        echo_json(versions)
    except SparkError as err:
        handle_error(err)
    except Exception as exc:
        handle_error(exc)


@services_cmd.command(name='delete', help='Delete services in a folder (irreversible - use with caution)')
@click.option('-f', '--folder', type=str, metavar='<FOLDER NAME>', help='Name of the folder to delete services from')
@click.argument('names', type=str, metavar='<SERVICE NAMES>', nargs=-1)
@header_option()
def delete_services(folder: str, names: list[str], headers: list[str]) -> None:
    profile = get_active_profile()

    if not names:
        raise click.BadParameter('at least one service name must be provided.')

    try:
        with Client(**profile.to_config()) as client:
            client.config.extra_headers.update(parse_pairs(headers))
            services = client.services
            for service in names:
                response = services.delete(folder=folder, service=service).data
                if response.get('status', '').lower() == 'success':  # type: ignore
                    click.echo(f'service deleted: {service}')

    except SparkError as err:
        handle_error(err)
    except Exception as exc:
        handle_error(exc)
