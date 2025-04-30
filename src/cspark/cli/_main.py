import click
from cspark.sdk import sdk_version

from ._commands import register_commands

__version__ = '0.1.0-beta'
__title__ = f'Coherent Spark CLI {__version__} (sdk v{sdk_version})'
__description__ = 'Interact with Coherent Spark APIs from the command line'


@click.group(invoke_without_command=True)
@click.pass_context
@click.version_option(__version__, '-v', '--version', message=__title__)
def main(ctx: click.Context) -> None:
    if ctx.invoked_subcommand is None:
        click.echo(f'{__description__}.\n')
        click.echo(ctx.get_help())
        click.echo('\nFor more details, visit https://docs.coherent.global/.')


register_commands(main)
