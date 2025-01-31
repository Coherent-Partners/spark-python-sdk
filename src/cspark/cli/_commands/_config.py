import json
import logging
import pathlib
from datetime import datetime
from typing import List, Optional, Union

import click
import yaml
from cspark.sdk import BaseUrl, LoggerOptions, SparkError
from cspark.sdk._validators import Validators
from cspark.sdk._version import sdk_logger
from InquirerPy import inquirer
from InquirerPy.validator import PathValidator
from rich.console import Console
from rich.text import Text

from .._utils import DATE_FORMAT, Profile, add_or_update_profile, delete_profile, get_active_profile, load_profiles
from ._api import AliasedGroup, parse_pairs

_SPARK_ENVS = ['uat.us', 'uat.eu', 'uat.jp', 'uat.ca', 'uat.au', 'us', 'ca', 'eu', 'jp', 'au', 'sit', 'dev', 'test']


@click.group(
    name='config',
    help='Manage configuration profiles',
    invoke_without_command=True,
    cls=AliasedGroup,
    aliases={'ls': 'list', 'rm': 'remove', 'del': 'remove'},
)
@click.option(
    '-p',
    '--profile',
    type=bool,
    is_flag=True,
    default=False,
    help='Add a configuration profile to connect to Spark',
)
@click.pass_context
def config_cmd(ctx: click.Context, profile: bool):
    if profile:
        click.echo('🚀 Setting up a new configuration profile')
        build_profile()
        return

    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@click.command(name='init', help='Start a new configuration profile')
@click.option(
    '-f',
    '--file',
    type=click.Path(exists=False, file_okay=True, dir_okay=False, writable=True, readable=True),
    metavar='<CONFIG PATH>',
    help='Path to the configuration file',
)
@click.option('--config', type=str, metavar='<JSON>', help='Configuration profile in JSON format')
def init_cmd(file: Union[pathlib.Path, str, None], config: Optional[str]):
    def msg(name):
        return f'[green]✓[/green] Profile [magenta]{name}[/magenta] created and set as active'

    console = Console()
    if file:
        profile = load_config_file(pathlib.Path(file))
        add_or_update_profile(profile)
        console.print(msg(profile.name))
    elif config:
        try:
            profile = Profile.from_dict(json.loads(config))
            add_or_update_profile(profile)
            console.print(msg(profile.name))
        except json.JSONDecodeError as err:
            Console().print('[red]✗[/red] Invalid JSON configuration')
            raise click.exceptions.Exit(1) from err
    else:
        # FIXME: improve welcome message.
        console.print('Welcome to Coherent Spark CLI!\n\n🚀 Build a configuration profile to connect to Spark')
        build_profile()


def load_config_file(file: pathlib.Path) -> Profile:
    if not file.exists():
        Console().print(f'[red]✗[/red] File not found: {file}')
        raise click.exceptions.Exit(1)

    try:
        if file.suffix.lower() in ['.yml', '.yaml']:
            with file.open() as f:
                config = yaml.safe_load(f)
        else:
            with file.open() as f:
                config = json.load(f)
        return Profile.from_dict(config)
    except (yaml.YAMLError, json.JSONDecodeError) as err:
        Console().print(f'[red]✗[/red] Invalid configuration file: {file}')
        raise click.exceptions.Exit(1) from err


def build_profile():
    profiles = load_profiles(is_init=True)

    profile_name = _collect_profile_name([p.name for p in profiles])
    base_url = _collect_base_url()
    auth = _collect_auth()
    logger = _collect_logger_options()
    timeout, max_retries, retry_interval = _collect_advanced_settings()

    now = datetime.now().isoformat()
    oauth = auth.get('oauth', {})
    profile = Profile(
        name=profile_name,
        is_active=True,
        created_at=now,
        updated_at=now,
        logger=logger,
        base_url=base_url,
        api_key=auth.get('api_key'),
        token=auth.get('token'),
        client_id=oauth.get('client_id') if isinstance(oauth, dict) else None,
        client_secret=oauth.get('client_secret') if isinstance(oauth, dict) else None,
        oauth_path=oauth if isinstance(oauth, str) else None,
        timeout=timeout,
        max_retries=max_retries,
        retry_interval=retry_interval,
    )

    add_or_update_profile(profile)
    Console().print(f'[green]✓[/green] Profile [magenta]{profile_name}[/magenta] created and set as active')


def _collect_profile_name(old_names: list[str]) -> str:
    return inquirer.text(  # type: ignore
        message='Enter profile name:',
        validate=lambda entry: len(entry) > 0 and entry not in old_names,
        filter=lambda entry: entry.strip(),
        invalid_message='Profile name is required and must be unique!',
    ).execute()


def _collect_base_url() -> str:
    options = {'full_url': 'Base URL', 'env_tenant': 'Environment and Tenant'}
    is_empty_str = Validators.empty_str().is_valid

    option = inquirer.select(  # type: ignore
        message='Define Spark connection settings using',
        choices=[*options.values()],
    ).execute()

    if option == options['full_url']:
        url = inquirer.text(  # type: ignore
            message='Enter base URL:',
            validate=Validators.base_url().is_valid,
            invalid_message='Invalid Spark URL',
            completer={'https://excel': None, 'coherent.global': None},
        ).execute()

        try:
            base_url = BaseUrl.of(url=url).full
        except SparkError:
            tenant = inquirer.text(  # type: ignore
                message='Tenant name is missing',
                validate=is_empty_str,
                invalid_message='Tenant name is required',
            ).execute()
            base_url = BaseUrl.of(url=url, tenant=tenant).full
    else:
        env = inquirer.text(  # type: ignore
            message='Enter environment:',
            validate=is_empty_str,
            invalid_message='Environment is required',
            completer={e: None for e in _SPARK_ENVS},
        ).execute()
        tenant = inquirer.text(  # type: ignore
            message='Enter tenant name:',
            validate=is_empty_str,
            invalid_message='Tenant name is required',
        ).execute()
        base_url = BaseUrl.of(env=env, tenant=tenant).full

    confirm_url = inquirer.confirm(  # type: ignore
        message=f'Is this base URL correct: {base_url}?', default=True
    ).execute()

    return base_url if confirm_url else _collect_base_url()


def _collect_auth():
    options = {'api_key': 'API key', 'bearer_token': 'Bearer token', 'oauth2': 'OAuth2 CCG'}
    scheme = inquirer.select(  # type: ignore
        message='Select authorization scheme:',
        choices=[*options.values()],
    ).execute()

    auth = {}
    is_empty_str = Validators.empty_str().is_valid

    if scheme == options['api_key']:
        api_key = inquirer.secret(message='Enter API key:', validate=is_empty_str).execute()  # type: ignore
        auth.update({'api_key': api_key})
    elif scheme == options['bearer_token']:
        token = inquirer.secret(message='Enter Bearer token:', validate=is_empty_str).execute()  # type: ignore
        auth.update({'token': token})
    else:
        oauth_method = inquirer.select(  # type: ignore
            message='Select OAuth2 CCG entry:',
            choices=['Path', 'Client ID and Secret'],
        ).execute()
        if oauth_method == 'Path':
            path = inquirer.filepath(  # type: ignore
                message='Enter path to OAuth2 CCG file:',
                validate=PathValidator(message='Invalid file path', is_file=True),
            ).execute()
            auth.update({'oauth': path})
        else:
            id = inquirer.secret(message='Enter client ID:', validate=is_empty_str).execute()  # type: ignore
            secret = inquirer.secret(message='Enter client secret:', validate=is_empty_str).execute()  # type: ignore
            auth.update({'oauth': {'client_id': id, 'client_secret': secret}})
    return auth


def _collect_logger_options() -> Union[bool, LoggerOptions]:
    enabled = inquirer.confirm(message='Enable logger?', default=False).execute()  # type: ignore

    if not enabled:
        return False

    colorful = inquirer.confirm(message='Should logs be colorful?', default=True).execute()  # type: ignore
    timestamp = inquirer.confirm(message='Should logs have timestamps?', default=True).execute()  # type: ignore
    context = inquirer.text(message='Enter logger context:', default=sdk_logger).execute()  # type: ignore
    level = inquirer.select(  # type: ignore
        message='Select log level:',
        default='DEBUG',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        filter=lambda choice: getattr(logging, choice),
    ).execute()

    return LoggerOptions(context=context, disabled=False, level=level, colorful=colorful, timestamp=timestamp)


def _collect_advanced_settings():
    should_configure = inquirer.confirm(  # type: ignore
        message='Do you want to configure advanced settings?', default=False
    ).execute()

    if not should_configure:
        return None, None, None

    timeout = inquirer.text(  # type: ignore
        message='Timeout in ms:',
        default='60000',
        validate=lambda entry: entry.isdigit(),
        invalid_message='Timeout must be a number!',
    ).execute()

    max_retries = inquirer.text(  # type: ignore
        message='Maximum retries:',
        default='2',
        validate=lambda entry: entry.isdigit(),
        invalid_message='Maximum retries must be a number!',
    ).execute()

    retry_interval = inquirer.text(  # type: ignore
        message='Retry interval in seconds:',
        default='1',
        validate=lambda entry: entry.isdigit(),
        invalid_message='Retry interval must be a number!',
    ).execute()

    return float(timeout), int(max_retries), float(retry_interval)


class ConfigSwitchCommand(click.Command):
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
            message='Select profile to switch to:',
            choices=[p.name for p in profiles],
        ).execute()

        for p in profiles:
            if p.name == selected:
                p.is_active = True
                add_or_update_profile(p)
                break

        Console().print(f'🔄 Profile switched to [magenta]{selected}[/magenta]!')


class ConfigSetCommand(click.Command):
    def __init__(self):
        super().__init__(
            name='set',
            help='Set configuration values of the active profile',
            options_metavar='',
            add_help_option=False,
            callback=self.set,
            params=[click.Argument(['values'], type=str, nargs=-1)],
        )

    def set(self, values: list[str]):
        updates = parse_pairs(values, sep='=', infer_type=True)
        if len(updates) == 0:
            raise click.UsageError('no configuration values to set; expecting <key>=<value> format')

        profile = get_active_profile()
        all_keys = profile.__dict__.keys()
        for key, val in updates.items():
            if key in all_keys:
                profile.__dict__[key] = val

        profile.updated_at = datetime.now().isoformat()
        add_or_update_profile(profile)
        Console().print(f'Profile [magenta]{profile.name}[/magenta] updated!')


class ConfigGetCommand(click.Command):
    def __init__(self):
        super().__init__(
            name='get',
            help='Read configuration values of the active profile',
            callback=self.get,
            options_metavar='',
            add_help_option=False,
            params=[click.Argument(['key'], type=str)],
        )

    def get(self, key: str):
        profile = get_active_profile()

        key = key.lower()
        if key in ['tenant', 'env', 'environment', 'url']:
            self._get_url_keys(key, profile)
        elif key in ['auth', 'oauth']:
            self._get_auth_keys(key, profile)
        elif key in profile.__dict__.keys():
            click.echo(profile.__dict__[key])
        else:
            raise click.UsageError(f'"{key}" is not valid key')

    def _get_url_keys(self, key: str, profile: Profile):
        url = profile.extract_url()
        if key == 'tenant':
            click.echo(url.tenant)
        elif key == 'url':
            click.echo(url.value)
        else:
            click.echo(url.env)

    def _get_auth_keys(self, key: str, profile: Profile):
        auth = profile.mask_auth(show=True)
        if key == 'auth':
            for k, v in auth.items():
                click.echo(f'{k}: {v}')
        else:
            config = profile.to_config()
            if 'oauth' in config:
                oauth = config['oauth']
                if isinstance(oauth, dict):
                    for k, v in oauth.items():
                        click.echo(f'{k}: {v}')
                else:
                    click.echo(oauth)
            else:
                click.echo(config.get('token'))


class ConfigListCommand(click.Command):
    def __init__(self):
        super().__init__(
            name='list',
            help='List configuration profiles',
            options_metavar='',
            add_help_option=False,
            callback=self.list,
            params=[
                click.Option(
                    ['-a', '--all'],
                    is_flag=True,
                    default=False,
                    type=bool,
                    help='Display details of all existing profiles',
                ),
                click.Option(
                    ['-v', '--verbose'],
                    is_flag=True,
                    default=False,
                    type=bool,
                    help='Display additional details of a profile',
                ),
            ],
        )

    def list(self, all: bool, verbose: bool):
        profiles = load_profiles()

        if not all and not verbose:
            self._show_profiles(profiles)
        elif all:
            for idx, profile in enumerate(profiles):
                self._display_profile(profile, nl=idx < len(profiles) - 1, verbose=verbose)
        else:
            for profile in profiles:
                if profile.is_active:
                    self._display_profile(profile, nl=False, verbose=verbose)
                    break

    def _show_profiles(self, profiles: List[Profile]):
        console = Console()
        for p in profiles:
            if p.is_active:
                console.print(f'* [magenta]{p.name}[/magenta]')
            else:
                console.print(f'  {p.name}')

    def _display_profile(self, profile: Profile, verbose: bool = False, nl: bool = False):
        url = profile.extract_url()

        console = Console()
        console.print(Text(f'{profile.name}', style=f"{'magenta' if profile.is_active else ''}"))
        console.print(f'  - base URL: {url.value}')
        console.print(f'  - tenant  : {url.tenant}')
        for key, value in profile.mask_auth().items():
            console.print(f'  - {key.ljust(8)}: {value}')

        if verbose:
            updated_at = datetime.fromisoformat(profile.updated_at).strftime(DATE_FORMAT)
            timeout = f'{profile.timeout / 1000.0} second(s)' if profile.timeout else 'None'
            retry_interval = f'{profile.retry_interval} second(s)' if profile.retry_interval else 'None'
            max_retries = f'up to {profile.max_retries} times' if profile.max_retries else 'None'
            console.print(f'  [cyan]other settings[/cyan]')
            console.print(f'    - logger     : [yellow]{"enabled" if profile.logger else "disabled"}[/yellow]')
            console.print(f'    - timeout    : {timeout}')
            console.print(f'    - interval   : {retry_interval}')
            console.print(f'    - max retries: {max_retries}')
            console.print(f'    - updated at : {updated_at}')

        if nl:
            console.print()


class ConfigRemoveCommand(click.Command):
    def __init__(self):
        super().__init__(
            name='remove',
            help='Remove a configuration profile',
            options_metavar='',
            add_help_option=False,
            callback=self.remove,
            params=[click.Option(['-f', '--force'], is_flag=True, default=False, help='Force removal of a profile')],
        )

    def remove(self, force: bool):
        profiles = load_profiles()
        console = Console()

        if len(profiles) == 1:
            if force:
                delete_profile(profiles[0])
                console.print('[red]✗[/red] Active profile removed')
            else:
                console.print(f'[yellow]WARNING: only one profile exists =>[/yellow] {profiles[0].name}')
                console.print('Use [green]--force[/green] to remove the active profile!')
                return
        else:
            selected = inquirer.select(  # type: ignore
                message='Select profile to remove:',
                choices=[p.name for p in profiles] + ['<Cancel>'],
            ).execute()

            for p in profiles:
                if p.name != selected:
                    continue

                if p.is_active and not force:
                    console.print(
                        f'[magenta]{selected}[/magenta] is the active profile; use [green]--force[/green] '
                        'to remove it or switch to another profile before removing it.\n'
                        'Use [green]cspark config switch[/green] to switch profiles.\n'
                        '[yellow]WARNING: Removing the active profile will fallback to the next available profile.[/yellow]'
                    )
                else:
                    delete_profile(p)
                    Console().print(f'[red]✗[/red] Profile [magenta]{selected}[/magenta] removed')
                break


config_cmd.add_command(ConfigSwitchCommand())
config_cmd.add_command(ConfigSetCommand())
config_cmd.add_command(ConfigGetCommand())
config_cmd.add_command(ConfigListCommand())
config_cmd.add_command(ConfigRemoveCommand())
