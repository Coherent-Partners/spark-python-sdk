from __future__ import annotations

import click
import cspark.sdk

from ._commands import register_commands


@click.group(invoke_without_command=True)
@click.pass_context
@click.option(
    '-v',
    '--version',
    type=bool,
    is_flag=True,
    default=False,
    help='Show the version and exit.',
)
def main(ctx, version: bool) -> None:
    if version:
        click.echo(f'Coherent Spark CLI v{cspark.sdk.__version__}')
        return

    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


register_commands(main)
