import pathlib
import re
from dataclasses import dataclass
from typing import List, Optional, Union

import click
import yaml
from cspark.sdk import BaseUrl, LoggerOptions, SparkError
from rich.console import Console

_HOME_DIR = pathlib.Path.home() / '.cspark'
_PROFILE_PATH = _HOME_DIR / 'profiles.yml'


class NoProfileError(click.UsageError):
    def __init__(self, ctx: Optional[click.Context] = None):
        msg = 'no profiles defined yet...\n'
        msg += 'Use `cspark init` to create and set an active profile.'
        super().__init__(msg, ctx=ctx)


@dataclass
class Profile:
    name: str
    is_active: bool
    created_at: str
    updated_at: str
    base_url: str
    api_key: Optional[str] = None
    token: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    oauth_path: Optional[str] = None
    timeout: Optional[float] = None
    max_retries: Optional[int] = None
    retry_interval: Optional[float] = None
    logger: Union[bool, LoggerOptions] = False

    def mask_auth(self, show: bool = False) -> dict[str, str]:
        auth = dict[str, str]()
        if self.api_key:
            auth['api_key'] = self.api_key if show else mask(self.api_key)
        if self.token:
            auth['token'] = self.token if show else mask(self.token)
        if self.oauth_path:
            auth['oauth'] = self.oauth_path
        elif self.client_id and self.client_secret:
            auth['oauth'] = (
                f'{self.client_id} / {self.client_secret}'
                if show
                else f'{mask(self.client_id)} / {mask(self.client_secret)}'
            )
        return auth

    def extract_url(self) -> BaseUrl:
        try:
            return BaseUrl.of(url=self.base_url)
        except SparkError as err:
            raise click.Abort(f'invalid base URL: {self.base_url}') from err

    def to_dict(self) -> dict:
        d = {
            'name': self.name,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'base_url': self.base_url,
            'auth': {},
            'timeout': self.timeout,
            'max_retries': self.max_retries,
            'retry_interval': self.retry_interval,
            'logger': self.logger.__dict__ if isinstance(self.logger, LoggerOptions) else False,
        }

        if self.api_key:
            d['auth']['api_key'] = self.api_key
        if self.token:
            d['auth']['token'] = self.token
        if self.client_id and self.client_secret:
            d['auth']['oauth'] = {'client_id': self.client_id, 'client_secret': self.client_secret}
        elif self.oauth_path:
            d['auth']['oauth'] = {'path': self.oauth_path}

        return {k: v for k, v in d.items() if v is not None}

    def _validate(self):
        if not self.base_url:
            raise click.UsageError('base_url is required')
        if not self.api_key and not self.token and not self.client_id and not self.oauth_path:
            raise click.UsageError('auth is required')
        if self.client_id and not self.client_secret:
            raise click.UsageError('client_secret is required')


def load_profiles(is_init: bool = False) -> List[Profile]:
    path = _PROFILE_PATH
    if not path.exists():
        create_profile()

    with path.open('r') as file:
        profile = yaml.load(file, Loader=yaml.FullLoader)

    version = profile.get('version', '1.0')
    active = profile.get('profile')
    accounts = profile.get('accounts', [])

    if re.match(r'^1\.\d+$', version):  # should match: 1.*
        profiles = [_parse_v1(account, active) for account in accounts]
        if not is_init and len(profiles) == 0:
            Console().print(
                '[red]ERROR: no profile has been set yet...[/red]'
                '\n💡 Use [green]cspark init[/green] to create and set an active profile.'
            )
            click.exceptions.Exit(2)
        return profiles
    raise ValueError(f'unsupported profile version: {version}')


def update_profile(updated: Profile):
    updated._validate()

    path = _PROFILE_PATH
    if not path.exists():
        create_profile()

    with path.open('r') as file:
        data = yaml.load(file, Loader=yaml.FullLoader)

    active_profile_name = data.get('profile', '')
    accounts = data.get('accounts', [])

    for i, account in enumerate(accounts):
        if account.get('name') == updated.name:
            accounts[i] = updated.to_dict()
            if updated.is_active and updated.name != active_profile_name:
                data['profile'] = updated.name
            break
    else:
        if updated.is_active:
            data['profile'] = updated.name
        accounts.append(updated.to_dict())

    data['accounts'] = accounts

    with path.open('w') as file:
        yaml.dump(data, file, sort_keys=False)


def delete_profile(profile: Union[str, Profile]):
    path = _PROFILE_PATH
    if not path.exists():
        return

    with path.open('r') as file:
        data = yaml.load(file, Loader=yaml.FullLoader)

    accounts = data.get('accounts', [])

    profile_name = profile if isinstance(profile, str) else profile.name
    if profile_name == data.get('profile', ''):
        names = [a.get('name') for a in accounts if a.get('name') != profile_name]
        if len(names) > 0:
            data['profile'] = names[0]  # set next available as active profile
        else:
            path.unlink()  # no more profiles; delete the file
            return

    for i, account in enumerate(accounts):
        if account.get('name') == profile_name:
            accounts.pop(i)
            break

    data['accounts'] = accounts
    with path.open('w') as file:
        yaml.dump(data, file, sort_keys=False)


def create_profile():
    path = _PROFILE_PATH
    if path.exists():
        return

    with path.open('w') as file:
        yaml.dump({'version': '1.0', 'profile': '', 'accounts': []}, file, sort_keys=False)


def get_active_profile() -> Optional[Profile]:
    profiles = load_profiles()
    for profile in profiles:
        if profile.is_active:
            return profile
    return None


def mask(s):
    return (s or '')[:4] + '*' * 12


def _parse_v1(account: dict, active: str) -> 'Profile':
    name = account.get('name', '')
    auth = account.get('auth', {})
    oauth = auth.get('oauth', {})
    return Profile(
        name=name,
        is_active=name == active,
        created_at=account.get('created_at', ''),
        updated_at=account.get('updated_at', ''),
        base_url=account.get('base_url', ''),
        api_key=auth.get('api_key'),
        token=auth.get('token'),
        client_id=oauth.get('client_id'),
        client_secret=oauth.get('client_secret'),
        oauth_path=oauth.get('path'),
        timeout=account.get('timeout'),
        max_retries=account.get('max_retries'),
        retry_interval=account.get('retry_interval'),
        logger=account.get('logger', False),
    )
