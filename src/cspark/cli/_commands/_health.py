from __future__ import annotations

import click
from cspark.sdk import Client, SparkError

from .._utils import get_active_profile
from ._api import AliasedGroup, echo_json, handle_error, header_option, parse_pairs


@click.group(
    name='health',
    help='Check Spark environment health',
    options_metavar='',
    cls=AliasedGroup,
    aliases={'status': 'check'},
)
def health_cmd():
    pass


@health_cmd.command(name='check', help='Check the health status of a Spark environment')
@header_option()
def check_health(headers: list[str]) -> None:
    profile = get_active_profile()

    try:
        with Client(**profile.to_config()) as client:
            client.config.extra_headers.update(parse_pairs(headers))
            response = client.health.check()
        echo_json(response.data)
    except SparkError as err:
        handle_error(err)
    except Exception as exc:
        handle_error(exc)


@health_cmd.command(name='ok', help='Return whether the Spark environment is healthy')
@header_option()
def health_ok(headers: list[str]) -> None:
    profile = get_active_profile()

    try:
        with Client(**profile.to_config()) as client:
            client.config.extra_headers.update(parse_pairs(headers))
            ok = client.health.ok()
        click.echo('true' if ok else 'false')
        if not ok:
            raise click.exceptions.Exit(1)
    except SparkError as err:
        handle_error(err)
    except click.exceptions.Exit:
        raise
    except Exception as exc:
        handle_error(exc)
