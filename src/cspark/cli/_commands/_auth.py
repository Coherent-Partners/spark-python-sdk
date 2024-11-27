import json
import pathlib
from datetime import datetime, timedelta
from typing import Union

import click
from cspark.sdk import Config, OAuth, SparkApiError
from rich.console import Console

from .._utils import DATE_FORMAT, HOME_DIR, Profile, get_active_profile, load_profiles


@click.group(name='auth', help='Manage Spark authorization with OAuth2 CCG', options_metavar='')
def auth_cmd():
    pass


def _friendly_time(seconds: Union[int, float]) -> str:
    if seconds < 60:
        return f'{int(seconds)} second{"s" if seconds > 1 else ""}'
    elif seconds < 3600:
        mins = seconds // 60
        return f'{int(mins)} min{"s" if mins > 1 else ""}'
    elif seconds < 86400:
        hrs = seconds // 3600
        mins_left = (seconds % 3600) // 60
        timeago = f'{int(hrs)} hr{"s" if hrs != 1 else ""}'
        if mins_left > 0:
            timeago = f'{timeago} {int(mins_left)} min{"s" if mins_left > 1 else ""}'
        return timeago
    else:
        days = seconds // 86400
        hrs_left = (seconds % 86400) // 3600
        timeago = f'{int(days)} day{"s" if days != 1 else ""}'
        if hrs_left > 0:
            timeago = f'{timeago} {int(hrs_left)} hr{"s" if hrs_left > 1 else ""}'
        return timeago


class AuthStatusCommand(click.Command):
    def __init__(self):
        super().__init__(
            name='status',
            help='Display authentication status of the active profile',
            callback=self.status,
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
        profiles = load_profiles()

        if all:
            for profile in profiles:
                self._display_status(profile, verbose=verbose)
        else:
            self._display_status(get_active_profile(), verbose=verbose)

    def _display_status(self, profile: Profile, verbose: bool):
        path = HOME_DIR / f'{profile.name}_auth.json'
        if path.exists():
            with path.open('r') as file:
                auth = json.load(file)
                auth.pop('profile')  # avoid duplicate keyword arguments
                self._display_auth_status(profile, verbose=verbose, **auth)
        else:
            self._display_unauth_status(profile)

    def _display_auth_status(
        self,
        profile: Profile,
        *,
        verbose: bool = False,
        created_at: str,
        access_token: str,
        expires_in: int,
        token_type: str,
        scope: str,
        **kwargs,  # noqa: ARG002
    ):
        url = profile.extract_url()
        is_expired, time_diff = self._calculate_expiration(created_at, expires_in)
        status = '[red]✗[/red] Logged out of' if is_expired else '[green]✓[/green] Logged in to'
        status_label = f'expired {time_diff} ago' if is_expired else f'expires in {time_diff}'
        hidden_token = f'{access_token[:4]}{"*" * 24 }{access_token[-4:]}'

        console = Console()
        console.print(f'{profile.name}', style='magenta' if profile.is_active else '')
        console.print(f'  {status} [cyan]{url.tenant} ({str(url.env).upper()})[/cyan]')
        console.print(f'  - Token: [bold]{hidden_token}[/bold] {"(expired)" if is_expired else ""}')
        if verbose:
            console.print(f'  - Status: {status_label}')
            console.print(f'  - Scope: [bold]{scope}[/bold]')
            console.print(f'  - Token type: [bold]{token_type}[/bold]')
            console.print(f'  - Last updated: {datetime.fromisoformat(created_at).strftime(DATE_FORMAT)}')

    def _display_unauth_status(self, profile: Profile):
        url = profile.extract_url()
        console = Console()
        console.print(f'{profile.name}', style='magenta' if profile.is_active else '')
        console.print(f'  [red]✗[/red] Not logged in to [cyan]{url.tenant} ({str(url.env).upper()})[/cyan]')

    def _calculate_expiration(self, issued_at: str, expires_in: int) -> tuple[bool, str]:
        expiration_time = datetime.fromisoformat(issued_at) + timedelta(seconds=expires_in)
        current_time = datetime.now()

        if current_time >= expiration_time:
            return True, _friendly_time((current_time - expiration_time).total_seconds())  # expired at ...
        else:
            return False, _friendly_time((expiration_time - current_time).total_seconds())  # expires in ...


class AuthLoginCommand(click.Command):
    def __init__(self):
        super().__init__(
            name='login',
            help='Use OAuth2 setup to retrieve or refresh access tokens',
            callback=self.login,
            params=[
                click.Option(
                    ['-r', '--refresh'],
                    is_flag=True,
                    default=False,
                    type=bool,
                    help='Force a refresh of the access token',
                ),
            ],
        )

    def login(self, refresh: bool):
        profile = get_active_profile()
        if not profile:
            return

        console = Console()
        if refresh:
            path = pathlib.Path(profile.oauth_path) if profile.oauth_path else None
            if path and path.exists():
                with path.open('r') as file:
                    oauth = json.load(file)
                    client_id = oauth.get('client_id') or oauth.get('clientId', '')
                    client_secret = oauth.get('client_secret') or oauth.get('clientSecret', '')
                self._login_with_oauth(profile, client_id, client_secret)
            elif profile.client_id and profile.client_secret:
                self._login_with_oauth(profile, profile.client_id, profile.client_secret)
            else:
                console.print('[red]✗[/red] No client ID or client secret found')
        else:
            path = HOME_DIR / f'{profile.name}_auth.json'
            if path.exists():
                with path.open('r') as file:
                    auth = json.load(file)

                    # NOTE: ideally, I should check the expiration time of the decoded token and
                    # make a decision based on that. However, for simplicity, I am using the
                    # the (local) time that the token was issued.
                    expiration_time = datetime.fromisoformat(auth['created_at']) + timedelta(seconds=auth['expires_in'])
                    current_time = datetime.now()

                    if current_time >= expiration_time:
                        console.print('[yellow]⚠[/yellow] Token has expired; refreshing token...')
                        self.login(refresh=True)
                    else:
                        expires_in = (expiration_time - current_time).total_seconds()
                        console.print(
                            f'[green]✓[/green] Token is still valid and will expire in about {_friendly_time(expires_in)}.'
                            '\nUse the [green]--refresh[/green] flag to force a token refresh'
                        )
            else:
                self.login(refresh=True)

    def _login_with_oauth(self, profile: Profile, client_id: str, client_secret: str):
        oauth = {'client_id': client_id, 'client_secret': client_secret}
        config = Config(
            base_url=profile.base_url,
            oauth=oauth,
            timeout=profile.timeout,
            max_retries=profile.max_retries,
            retry_interval=profile.retry_interval,
            logger=profile.logger,
        )

        console = Console()
        try:
            access_token = OAuth(oauth).retrieve_token(config)

            path = HOME_DIR / f'{profile.name}_auth.json'
            with path.open('w') as file:
                now = datetime.now().isoformat()
                json.dump({'profile': profile.name, 'created_at': now, **access_token.__dict__}, file, sort_keys=False)

            url = profile.extract_url()
            console.print(f'[green]✓[/green] Logged in to [cyan]{url.tenant} ({str(url.env).upper()})[/cyan]')
        except SparkApiError as err:
            if err.status == 401:
                console.print('[red]✗[/red] failed to log in to Spark due to invalid credentials')
            else:
                console.print(f'[red]✗[/red] failed to log in to Spark API...\nMore details: \n{err}')
        except Exception:
            console.print('[red]✗[/red] cannot to log in to Spark API')

    def _extract_creds(self):
        pass


class AuthLogoutCommand(click.Command):
    def __init__(self):
        super().__init__(
            name='logout',
            help='Remove the authentication token for the active profile',
            options_metavar='',
            add_help_option=False,
            callback=self.logout,
        )

    def logout(self):
        profile = get_active_profile()
        url = profile.extract_url()
        tenant = f'[cyan]{url.tenant} ({str(url.env).upper()})[/cyan]'

        path = HOME_DIR / f'{profile.name}_auth.json'
        if path.exists():
            path.unlink()
            Console().print(f'[green]✓[/green] Logged out of {tenant}')
        else:
            Console().print(f'[red]✗[/red] No active session for {tenant}')


auth_cmd.add_command(AuthLoginCommand())
auth_cmd.add_command(AuthLogoutCommand())
auth_cmd.add_command(AuthStatusCommand())
