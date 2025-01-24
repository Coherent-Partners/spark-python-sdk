import click

from ._auth import auth_cmd
from ._config import config_cmd, init_cmd
from ._folders import folders_cmd
from ._services import services_cmd
from ._versions import versions_cmd


def register_commands(cli: click.Group) -> None:
    cli.add_command(init_cmd)
    cli.add_command(config_cmd)
    cli.add_command(auth_cmd)
    cli.add_command(versions_cmd)
    cli.add_command(services_cmd)
    cli.add_command(folders_cmd)
