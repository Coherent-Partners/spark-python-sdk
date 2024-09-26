import json
import pathlib

import click
from InquirerPy import inquirer
from rich.console import Console
from rich.text import Text

from .._utils import Profile, load_profiles, update_profile, get_active_profile


@click.group(name='auth', help='Manage authentication and authorization')
def auth_cmd():
    pass


class AuthStatusCommand(click.Command):
    def __init__(self):
        super().__init__(
            name='status',
            help='Check the status of the current authorization configuration',
            callback=self.status,
            options_metavar='',
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
        profiles = load_profiles()

        if all:
            for profile in profiles:
                self._display_profile(profile)
        else:
            profile = get_active_profile()
            if profile:
                self._display_profile(profile)
            else:
                raise click.UsageError('no active profile found')

    def _display_profile(self, profile: Profile):
        url = profile.extract_url()

        console = Console()
        console.print(Text(f'{profile.name}', style=f"bold {'green' if profile.is_active else ''}"))
        console.print(f'  - base URL: {url.value}')
        console.print(f'  - tenant  : {url.tenant}')
        for key, value in profile.mask_auth().items():
            console.print(f'  - {key.ljust(8)}: {value}')
        console.print()


class AuthSwitchCommand(click.Command):
    def __init__(self):
        super().__init__(
            name='switch',
            help='Switch between different configuration profiles',
            options_metavar='',
            add_help_option=False,
            callback=self.switch,
        )

    def switch(self):
        profiles = load_profiles()
        selected = inquirer.select(  # type: ignore
            message='Select a profile to switch to:',
            qmark='🔄',
            amark='✅',
            choices=[p.name for p in profiles],
        ).execute()

        for p in profiles:
            if p.name == selected:
                p.is_active = True
                update_profile(p)
                break

        Console().print(f'Profile switched to [magenta]{selected}[/magenta]!')


class AuthLoginCommand(click.Command):
    def __init__(self):
        super().__init__(
            name='login',
            help='Use OAuth2 to retrieve or refresh access tokens',
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
                    ['--oauth-path'],
                    help='Path to the OAuth2 client credentials file',
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
        click.echo(f'Logging out and removing authentication file at {force}')


auth_cmd.add_command(AuthLoginCommand())
auth_cmd.add_command(AuthLogoutCommand())
auth_cmd.add_command(AuthStatusCommand())
auth_cmd.add_command(AuthSwitchCommand())
