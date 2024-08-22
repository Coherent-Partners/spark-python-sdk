import json
import pathlib

import click


@click.group(name='auth', help='Manages authentication')
def auth_group():
    pass


class AuthLoginCommand(click.Command):
    def __init__(self):
        super().__init__(
            name='login',
            help='Use OAuth2 to retrieve or refresh access token',
            callback=self.login,
            params=[
                click.Option(
                    ['-i', '--client-id'],
                    type=str,
                    help='Client ID to use for OAuth2 access token generation',
                    required=False,
                ),
                click.Option(
                    ['-s', '--client-secret'],
                    type=str,
                    help='Client Secret to use for OAuth2 access token generation',
                    required=False,
                    hide_input=True,
                ),
                click.Option(
                    ['--auth-path'],
                    help='Path to the authentication file',
                    default=pathlib.Path.home() / '.cspark' / 'auth.json',
                    type=click.Path(exists=False, file_okay=True, dir_okay=False, writable=True, readable=True),
                ),
            ],
        )

    def login(self, client_id: str, client_secret: str, auth_path: pathlib.Path):
        auth_path = pathlib.Path(auth_path)
        if auth_path.exists():
            click.echo(
                f'Logging in using authentication file at {auth_path}:\n'
                f'{json.dumps(json.load(auth_path.open()), indent=2)}'
            )
        elif client_id:
            if not client_secret:
                client_secret = click.prompt('Client Secret', hide_input=True)
            click.echo(f'Logging in with Client ID: {client_id} and Client Secret: {client_secret}')
        else:
            raise click.UsageError('You must provide either --auth-path or --client-id and --client-secret')


class AuthLogoutCommand(click.Command):
    def __init__(self):
        super().__init__(
            name='logout',
            help='Invalidate the existing authorization configuration if any',
            callback=self.logout,
            params=[
                click.Option(
                    ['-f', '--force'],
                    is_flag=True,
                    default=False,
                    type=bool,
                    help='Force removal of the authorization configuration',
                )
            ],
        )

    def logout(self, force: bool):
        click.echo(f'Logging out and removing authentication file at {force}')


class AuthStatusCommand(click.Command):
    def __init__(self):
        super().__init__(
            name='status',
            help='Check the status of the current authorization configuration',
            callback=self.status,
            params=[
                click.Option(
                    ['-a', '--all'],
                    is_flag=True,
                    default=False,
                    type=bool,
                    help='Show all details of the authentication status',
                )
            ],
        )

    def status(self, all: bool):
        click.echo(f'Checking status of authentication file {all}')


auth_group.add_command(AuthLoginCommand())
auth_group.add_command(AuthLogoutCommand())
auth_group.add_command(AuthStatusCommand())
