from __future__ import annotations

import click
from cspark.sdk import Client, SparkError
from InquirerPy import inquirer

from .._utils import get_active_profile
from ._api import AliasedGroup, echo_json, handle_error, header_option, json_parse, parse_pairs


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

    try:
        with Client(**profile.to_config()) as client:
            client.config.extra_headers.update(parse_pairs(headers))
            response = client.folders.find(**json_parse(data)).data

        output = response['data']  # type: ignore
        if name_only:
            output = [item['name'] for item in output]  # type: ignore

        echo_json(output)
    except SparkError as err:
        handle_error(err)
    except Exception as exc:
        handle_error(exc)


@folders_cmd.command(name='create', help='Create a new folder')
@click.argument('name', type=str, metavar='<FOLDER NAME>')
@click.option('--description', type=str, metavar='<TEXT>', help='Folder description')
@click.option('--category', type=str, metavar='<NAME>', help='Folder category (default: Other)')
@click.option('--status', type=str, metavar='<STATUS>', help='Folder status (default: Design)')
@click.option('--start-date', type=str, metavar='<DATE>', help='Effective start date')
@click.option('--launch-date', type=str, metavar='<DATE>', help='Launch date')
@header_option()
def create_folder(
    name: str,
    description: str,
    category: str,
    status: str,
    start_date: str,
    launch_date: str,
    headers: list[str],
) -> None:
    profile = get_active_profile()

    try:
        with Client(**profile.to_config()) as client:
            client.config.extra_headers.update(parse_pairs(headers))
            response = client.folders.create(
                name,
                description=description,
                category=category,
                status=status,
                start_date=start_date,
                launch_date=launch_date,
            )
        echo_json(response.data)
    except SparkError as err:
        handle_error(err)
    except Exception as exc:
        handle_error(exc)


@folders_cmd.command(name='update', help='Update an existing folder')
@click.argument('id', type=str, metavar='<FOLDER ID>')
@click.option('--description', type=str, metavar='<TEXT>', help='Folder description')
@click.option('--category', type=str, metavar='<NAME>', help='Folder category')
@click.option('--start-date', type=str, metavar='<DATE>', help='Effective start date')
@click.option('--launch-date', type=str, metavar='<DATE>', help='Launch date')
@header_option()
def update_folder(
    id: str,
    description: str,
    category: str,
    start_date: str,
    launch_date: str,
    headers: list[str],
) -> None:
    profile = get_active_profile()

    try:
        with Client(**profile.to_config()) as client:
            client.config.extra_headers.update(parse_pairs(headers))
            response = client.folders.update(
                id,
                description=description,
                category=category,
                start_date=start_date,
                launch_date=launch_date,
            )
        echo_json(response.data)
    except SparkError as err:
        handle_error(err)
    except Exception as exc:
        handle_error(exc)


@folders_cmd.command(name='exists', help='Check whether a folder exists')
@click.argument('name', type=str, metavar='<FOLDER NAME>')
@header_option()
def folder_exists(name: str, headers: list[str]) -> None:
    profile = get_active_profile()

    try:
        with Client(**profile.to_config()) as client:
            client.config.extra_headers.update(parse_pairs(headers))
            exists = client.folders.exists(name)
        click.echo('true' if exists else 'false')
        if not exists:
            raise click.exceptions.Exit(1)
    except SparkError as err:
        handle_error(err)
    except click.exceptions.Exit:
        raise
    except Exception as exc:
        handle_error(exc)


@folders_cmd.command(name='delete', help='Delete a folder (and all its services)')
@click.argument('names', type=str, metavar='<FOLDER NAMES>', nargs=-1)
@header_option()
def delete_folders(names: list[str], headers: list[str]) -> None:
    profile = get_active_profile()

    if not names:
        raise click.BadParameter('at least one folder name must be provided.')

    try:
        with Client(**profile.to_config()) as client:
            client.config.extra_headers.update(parse_pairs(headers))
            folders_api = client.folders
            for folder in names:
                confirmed = inquirer.confirm(  # type: ignore
                    message=f'Are you sure you want to delete "{folder}" and all its services?', default=False
                ).execute()
                if not confirmed:
                    click.echo(f'folder skipped: {folder}')
                    continue

                response = folders_api.delete(folder).data
                if response.get('status', '').lower() == 'success':  # type: ignore
                    click.echo(f'folder deleted: {folder}')

    except SparkError as err:
        handle_error(err)
    except Exception as exc:
        handle_error(exc)
