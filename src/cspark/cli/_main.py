from __future__ import annotations

import click
import cspark.sdk

from ._commands import register_commands


@click.group(invoke_without_command=True)
@click.pass_context
@click.version_option(message=f'Coherent Spark CLI v{cspark.sdk.__version__}')
def main(ctx: click.Context) -> None:
    if ctx.invoked_subcommand is None:
        click.echo('Interact with Coherent Spark APIs from the command line.\n')
        click.echo(ctx.get_help())
        click.echo('\nFor more details, visit https://docs.coherent.global.')


register_commands(main)
