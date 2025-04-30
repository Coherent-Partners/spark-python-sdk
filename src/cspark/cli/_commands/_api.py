import json
from typing import Any, Callable, Mapping, Optional, Union

import click
from cspark.sdk import ApiResource, Uri


def header_option(**kwargs: Any) -> Callable:
    """Define a decorator that applies headers to a command"""

    def decorator(func: Union[Callable, click.Command]) -> Union[Callable, click.Command]:
        return click.option(
            '-H',
            '--header',
            'headers',
            type=str,
            multiple=True,  # allows multiple headers
            help='Headers to send with the request (e.g., "x-my-header: value")',
            metavar='<HEADER>',
            **kwargs,
        )(func)

    return decorator


def params_option(**kwargs: Any) -> Callable:
    """Define a decorator that applies parameters to a command"""

    def decorator(func: Union[Callable, click.Command]) -> Union[Callable, click.Command]:
        return click.option(
            '-p',
            '--param',
            'params',
            type=str,
            multiple=True,  # allows multiple params
            help='Additional parameters (or metadata) supported',
            metavar='<PARAM>',
            **kwargs,
        )(func)

    return decorator


def parse_pairs(pairs: list[str], *, sep: str = ':', infer_type: bool = False) -> dict:
    """Parse a list of key-value pairs into a dictionary"""

    def _infer_type(value: str):
        val = value.strip().lower()
        if val == 'true':
            return True
        elif val == 'false':
            return False
        try:
            return float(val) if '.' in val else int(val)
        except ValueError:
            return value  # default to string

    parsed = {}
    for pair in pairs:
        try:
            key, value = pair.split(sep, 1)
            parsed[key.strip()] = _infer_type(value.strip()) if infer_type else value.strip()
        except Exception:
            pass

    return parsed


def json_parse(data: str, fallback: Optional[Any] = None) -> dict:
    try:
        return json.loads(data)
    except Exception:
        return fallback or {}


class Services(ApiResource):
    def get(self, folder: str, data: Optional[str] = None):
        endpoint = f'product/{folder}/engines'
        url = Uri.of(base_url=self.config.base_url.value, version='api/v1', endpoint=endpoint)
        body = {'page': 1, 'pageSize': 100, 'search': [], 'sort': 'name1'}
        return self.request(url, method='POST', body=body.update(json_parse(data)) if data else body)


class AliasedGroup(click.Group):
    """A click Group that allows aliases to be defined"""

    def __init__(self, *, name: str, aliases: Optional[Mapping[str, str]] = None, **attrs: Any) -> None:
        self.aliases = aliases or {}
        super().__init__(name=name, **attrs)

    def get_command(self, ctx: click.Context, cmd_name: str):
        rv = click.Group.get_command(self, ctx, cmd_name)
        if rv is not None:
            return rv

        if cmd_name in self.aliases:
            actual_cmd = self.aliases[cmd_name]
            return click.Group.get_command(self, ctx, actual_cmd)

        # NOTE: is this a good idea?
        # Alternative option: if we did not find an explicit alias we
        # allow automatic abbreviation of the command.  "execute" for
        # instance will match "exec".  We only allow that however if
        # there is only one command.
        # matches = [x for x in self.list_commands(ctx) if x.lower().startswith(cmd_name.lower())]

        # if not matches:
        #     return None
        # elif len(matches) == 1:
        #     return click.Group.get_command(self, ctx, matches[0])
        # ctx.fail(f"too many matches: {', '.join(sorted(matches))}")
        return None

    def resolve_command(self, ctx, args):
        # always return the command's name, not the alias
        _, cmd, args = super().resolve_command(ctx, args)
        return cmd.name, cmd, args  # type: ignore
