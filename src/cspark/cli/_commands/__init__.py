import click

from ._auth import auth_group
from ._services import services_group


def register_commands(cli: click.Group) -> None:
    cli.add_command(auth_group)
    cli.add_command(services_group)
