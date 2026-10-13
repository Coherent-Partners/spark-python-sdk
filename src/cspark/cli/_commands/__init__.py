import click

from ._auth import auth_cmd
from ._config import config_cmd, init_cmd
from ._files import files_cmd
from ._folders import folders_cmd
from ._health import health_cmd
from ._impex import impex_cmd
from ._logs import logs_cmd
from ._services import services_cmd
from ._transforms import transforms_cmd
from ._versions import versions_cmd
from ._wasm import wasm_cmd


def register_commands(cli: click.Group) -> None:
    cli.add_command(init_cmd)
    cli.add_command(config_cmd)
    cli.add_command(auth_cmd)
    cli.add_command(health_cmd)
    cli.add_command(versions_cmd)
    cli.add_command(services_cmd)
    cli.add_command(folders_cmd)
    cli.add_command(transforms_cmd)
    cli.add_command(logs_cmd)
    cli.add_command(impex_cmd)
    cli.add_command(wasm_cmd)
    cli.add_command(files_cmd)
