import json
import pathlib

import click
from InquirerPy import inquirer


@click.group(name='auth', help='Manage Spark authorization settings', options_metavar='')
def auth_cmd():
    pass


class AuthStatusCommand(click.Command):
    def __init__(self):
        super().__init__(
            name='status',
            help='Display authentication status of the active profile',
            callback=self.status,
            options_metavar='',
            params=[
                click.Option(
                    ['-a', '--all'],
                    is_flag=True,
                    default=False,
                    type=bool,
                    help='Display authentication status of all the profiles',
                ),
                click.Option(
                    ['-v', '--verbose'],
                    is_flag=True,
                    default=False,
                    type=bool,
                    help='Display additional details of the authentication status',
                ),
            ],
        )

    def status(self, all: bool, verbose: bool):
        pass


class AuthLoginCommand(click.Command):
    def __init__(self):
        super().__init__(
            name='login',
            help='Use OAuth2 setup to retrieve or refresh access tokens',
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
                    ['--path'],
                    help='Path to the OAuth2 client credentials file',
                    type=click.Path(exists=False, file_okay=True, dir_okay=False, writable=True, readable=True),
                ),
            ],
        )

    def login(self, client_id: str, client_secret: str, path: pathlib.Path):
        path = pathlib.Path(path)
        if path.exists():
            click.echo(
                f'Logging in using authentication file at {path}:\n' f'{json.dumps(json.load(path.open()), indent=2)}'
            )
        elif client_id:
            if not client_secret:
                client_secret = inquirer.secret(  # type: ignore
                    message='client secret:',
                    validate=lambda entry: len(entry) > 4,
                    filter=lambda entry: entry.strip(),
                    invalid_message='Client secret is required when using client ID',
                    qmark='🔑',
                    amark='🔒',
                ).execute()
            click.echo(f'Logging in with Client ID: {client_id} and Client Secret: {client_secret}')
        else:
            raise click.UsageError('You must provide either --oauth-path or --client-id and --client-secret')


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
        click.echo(f'Logging out and removing authentication file (forced: {force})')


auth_cmd.add_command(AuthLoginCommand())
auth_cmd.add_command(AuthLogoutCommand())
auth_cmd.add_command(AuthStatusCommand())
