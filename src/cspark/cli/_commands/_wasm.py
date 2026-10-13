from __future__ import annotations

import pathlib
from typing import Optional

import click
from cspark.sdk import Client, SparkError

from .._utils import get_active_profile
from ._api import AliasedGroup, handle_error, header_option, output_option, parse_pairs, spinner, write_response_file


@click.group(
    name='wasm',
    help='Download WASM / Nodegen packages for Spark services',
    options_metavar='',
    cls=AliasedGroup,
    aliases={'dl': 'download'},
)
def wasm_cmd():
    pass


@wasm_cmd.command(name='download', help='Download a WASM package for a service')
@click.argument('uri', type=str, metavar='<SERVICE URI>')
@click.option('--public', is_flag=True, default=False, help='Download from the public endpoint')
@output_option()
@header_option()
def download_wasm(uri: str, public: bool, output: Optional[pathlib.Path], headers: list[str]) -> None:
    profile = get_active_profile()

    try:
        with Client(**profile.to_config()) as client:
            client.config.extra_headers.update(parse_pairs(headers))
            with spinner(f'Downloading WASM for {uri}...'):
                response = client.wasm.download(uri, public=public)
        path = write_response_file(response, output, default_name=f'{uri.replace("/", "_")}.zip')
        click.echo(f'wrote {path}')
    except SparkError as err:
        handle_error(err)
    except Exception as exc:
        handle_error(exc)
