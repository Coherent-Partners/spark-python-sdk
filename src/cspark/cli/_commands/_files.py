from __future__ import annotations

import pathlib
from typing import Optional
from urllib.parse import urlparse

import click
from cspark.sdk import Client, SparkError

from .._utils import get_active_profile
from ._api import AliasedGroup, handle_error, header_option, output_option, parse_pairs, spinner, write_response_file


@click.group(
    name='files',
    help='Download files using authenticated Spark credentials',
    options_metavar='',
    cls=AliasedGroup,
    aliases={'dl': 'download'},
)
def files_cmd():
    pass


@files_cmd.command(name='download', help='Download a file from a URL')
@click.argument('url', type=str, metavar='<URL>')
@output_option()
@header_option()
def download_file(url: str, output: Optional[pathlib.Path], headers: list[str]) -> None:
    profile = get_active_profile()
    parsed = urlparse(url)
    default_name = pathlib.Path(parsed.path).name or 'download.bin'

    try:
        with Client(**profile.to_config()) as client:
            client.config.extra_headers.update(parse_pairs(headers))
            with spinner('Downloading file...'):
                response = client.files.download(url)
        path = write_response_file(response, output, default_name=default_name)
        click.echo(f'file downloaded: {path}')
    except SparkError as err:
        handle_error(err)
    except Exception as exc:
        handle_error(exc)
