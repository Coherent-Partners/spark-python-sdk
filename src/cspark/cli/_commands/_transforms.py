from __future__ import annotations

import pathlib
from typing import Optional

import click
from cspark.sdk import Client, SparkError, Transform

from .._utils import get_active_profile
from ._api import (
    AliasedGroup,
    echo_json,
    handle_error,
    header_option,
    json_parse,
    parse_pairs,
    read_json_input,
)


@click.group(
    name='transforms',
    help='Manage Spark transforms',
    options_metavar='',
    cls=AliasedGroup,
    aliases={'ls': 'list', 'del': 'delete'},
)
def transforms_cmd():
    pass


def _load_transform(
    data: Optional[str] = None,
    file: Optional[pathlib.Path] = None,
) -> Transform:
    payload = read_json_input(data, file=file)
    if payload is None:
        raise click.BadParameter('transform definition required via --data or --file')
    if isinstance(payload, str):
        return Transform(**json_parse(payload))
    if not isinstance(payload, dict):
        raise click.BadParameter('transform definition must be a JSON object')
    return Transform(
        schema=payload.get('schema'),
        api_version=payload.get('api_version'),
        inputs=payload.get('inputs'),
        outputs=payload.get('outputs'),
        extras=payload.get('extras'),
    )


@transforms_cmd.command(name='list', help='List transforms in a folder')
@click.argument('folder', type=str, metavar='<FOLDER NAME>')
@click.option('-d', '--data', type=str, metavar='<JSON>', help='Pagination data to send with the request')
@header_option()
def list_transforms(folder: str, data: str, headers: list[str]) -> None:
    profile = get_active_profile()

    try:
        with Client(**profile.to_config()) as client:
            client.config.extra_headers.update(parse_pairs(headers))
            response = client.transforms.list(folder, **json_parse(data))
        echo_json(response.data)
    except SparkError as err:
        handle_error(err)
    except Exception as exc:
        handle_error(exc)


@transforms_cmd.command(name='get', help='Get a transform by URI')
@click.argument('uri', type=str, metavar='<TRANSFORM URI>')
@header_option()
def get_transform(uri: str, headers: list[str]) -> None:
    profile = get_active_profile()

    try:
        with Client(**profile.to_config()) as client:
            client.config.extra_headers.update(parse_pairs(headers))
            response = client.transforms.get(uri)
        echo_json(response.data)
    except SparkError as err:
        handle_error(err)
    except Exception as exc:
        handle_error(exc)


@transforms_cmd.command(name='save', help='Save (create or update) a transform')
@click.option('-f', '--folder', required=True, type=str, metavar='<FOLDER>', help='Folder name')
@click.option('-n', '--name', required=True, type=str, metavar='<NAME>', help='Transform name')
@click.option('-d', '--data', type=str, metavar='<JSON>', help='Transform definition as JSON')
@click.option(
    '--file',
    'file_path',
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=pathlib.Path),
    metavar='<FILE>',
    help='Path to a JSON transform definition',
)
@header_option()
def save_transform(
    folder: str,
    name: str,
    data: Optional[str],
    file_path: Optional[pathlib.Path],
    headers: list[str],
) -> None:
    profile = get_active_profile()
    transform = _load_transform(data, file_path)

    try:
        with Client(**profile.to_config()) as client:
            client.config.extra_headers.update(parse_pairs(headers))
            response = client.transforms.save(folder=folder, name=name, transform=transform)
        echo_json(response.data)
    except SparkError as err:
        handle_error(err)
    except Exception as exc:
        handle_error(exc)


@transforms_cmd.command(name='validate', help='Validate a transform definition')
@click.option('-d', '--data', type=str, metavar='<JSON>', help='Transform definition as JSON')
@click.option(
    '--file',
    'file_path',
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=pathlib.Path),
    metavar='<FILE>',
    help='Path to a JSON transform definition',
)
@header_option()
def validate_transform(data: Optional[str], file_path: Optional[pathlib.Path], headers: list[str]) -> None:
    profile = get_active_profile()
    transform = _load_transform(data, file_path)

    try:
        with Client(**profile.to_config()) as client:
            client.config.extra_headers.update(parse_pairs(headers))
            response = client.transforms.validate(transform)
        echo_json(response.data)
    except SparkError as err:
        handle_error(err)
    except Exception as exc:
        handle_error(exc)


@transforms_cmd.command(name='delete', help='Delete a transform')
@click.argument('uri', type=str, metavar='<TRANSFORM URI>')
@header_option()
def delete_transform(uri: str, headers: list[str]) -> None:
    profile = get_active_profile()

    try:
        with Client(**profile.to_config()) as client:
            client.config.extra_headers.update(parse_pairs(headers))
            response = client.transforms.delete(uri)
        echo_json(response.data)
    except SparkError as err:
        handle_error(err)
    except Exception as exc:
        handle_error(exc)
