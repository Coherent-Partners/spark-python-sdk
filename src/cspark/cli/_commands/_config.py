from __future__ import annotations

import json
import logging
from datetime import datetime

import click
from cspark.sdk import BaseUrl, LoggerOptions, SparkError
from cspark.sdk._validators import Validators
from cspark.sdk._version import sdk_logger
from InquirerPy import inquirer
from InquirerPy.validator import PathValidator
from rich.console import Console

from .._utils import Profile, load_profiles, update_profile, get_active_profile


@click.group(name='config', help='Set up Spark configuration profiles', invoke_without_command=True)
@click.option(
    '-p',
    '--profile',
    type=bool,
    is_flag=True,
    default=False,
    help='Add a configuration profile to use',
)
@click.pass_context
def config_cmd(ctx: click.Context, profile: bool):
    if profile:
        click.echo('🚀 Setting up a new configuration profile')
        build_profile()
        return

    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


def build_profile():
    profiles = load_profiles()

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

    update_profile(profile)
    Console().print(f'[green]✓[/green] Profile [magenta]{profile_name}[/magenta] created and set as active')


def _collect_profile_name(old_names: list[str]) -> str:
    return inquirer.text(  # type: ignore
        message='Enter profile name:',
        validate=lambda entry: len(entry) > 0 and entry not in old_names,
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
        envs = ['uat.us', 'uat.eu', 'uat.jp', 'uat.ca', 'uat.au', 'us', 'ca', 'eu', 'jp', 'au', 'sit', 'dev', 'test']
        env = inquirer.text(  # type: ignore
            message='Enter environment:',
            validate=is_empty_str,
            invalid_message='Environment is required',
            completer={e: None for e in envs},
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

    while not confirm_url:
        base_url = _collect_base_url()
        confirm_url = inquirer.confirm(  # type: ignore
            message=f'Is this base URL correct: {base_url}?', default=True
        ).execute()
    return base_url


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


def _collect_logger_options() -> bool | LoggerOptions:
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


class ConfigSetCommand(click.Command):
    def __init__(self):
        super().__init__(
            name='set',
            help='Set configuration values',
            options_metavar='',
            add_help_option=False,
            callback=self.set,
            params=[click.Argument(['values'], type=str, nargs=-1)],
        )

    def set(self, values: list[str]):
        updates = {}
        for value in values:
            try:
                key, val = value.split('=')
                updates[key] = val
            except ValueError:
                raise click.UsageError(f'invalid format: {value}; expected format: <key>=<value>')

        if len(updates) == 0:
            raise click.UsageError('no configuration values to set')

        profile = get_active_profile()
        if profile is None:
            raise click.UsageError('no profile has been set yet')

        all_keys = profile.__dict__.keys()
        for key, val in updates.items():
            if key in all_keys:
                profile.__dict__[key] = val

        profile.updated_at = datetime.now().isoformat()
        update_profile(profile)
        Console().print(f'Profile [magenta]{profile.name}[/magenta] updated!')


class ConfigGetCommand(click.Command):
    def __init__(self):
        super().__init__(
            name='get',
            help='Read configuration values',
            callback=self.get,
            options_metavar='',
            add_help_option=False,
            params=[click.Argument(['key'], type=str)],
        )

    def get(self, key: str):
        profile = get_active_profile()
        if profile is None:
            raise click.UsageError('no profile has been set yet')

        key = key.lower()
        if key in ['tenant', 'env', 'environment', 'url']:
            self._get_url_keys(key, profile)
            return

        if key in profile.__dict__.keys():
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


class ConfigListCommand(click.Command):
    def __init__(self):
        super().__init__(
            name='list',
            help='List configuration profiles\' names',
            options_metavar='',
            add_help_option=False,
            callback=self.list
        )

    def list(self):
        profiles = load_profiles()
        console = Console()
        for p in profiles:
            if p.is_active:
                console.print(f'* [magenta]{p.name}[/magenta]')
            else:
                console.print(f'  {p.name}')


config_cmd.add_command(ConfigSetCommand())
config_cmd.add_command(ConfigGetCommand())
config_cmd.add_command(ConfigListCommand())
