from __future__ import annotations

import click
from cspark.sdk import Client, SparkError

from .._utils import get_active_profile
from ._api import AliasedGroup, echo_json, handle_error, header_option, parse_pairs


@click.group(
    name='versions',
    help='Interact with versions of a Spark service',
    options_metavar='',
    cls=AliasedGroup,
    aliases={'ls': 'list', 'get': 'list'},
)
def versions_cmd():
    pass


@versions_cmd.command(name='list', help='List available versions of a service')
@click.argument('uri', type=str, metavar='<SERVICE URI>')
@header_option()
@click.option('--latest', is_flag=True, default=False, help='Show only the latest version')
def list_versions(uri: str, headers: list[str], latest: bool) -> None:
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
