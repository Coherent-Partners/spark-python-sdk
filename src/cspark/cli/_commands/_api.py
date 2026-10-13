from __future__ import annotations

import json
import pathlib
import sys
from contextlib import contextmanager
from typing import Any, Callable, Iterator, Mapping, Optional, Union

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table


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


def output_option(**kwargs: Any) -> Callable:
    """Define a decorator for writing binary/file output."""

    def decorator(func: Union[Callable, click.Command]) -> Union[Callable, click.Command]:
        return click.option(
            '-o',
            '--output',
            'output',
            type=click.Path(file_okay=True, dir_okay=False, writable=True, path_type=pathlib.Path),
            metavar='<FILE>',
            help='Write response content to a file',
            **kwargs,
        )(func)

    return decorator


def format_option(**kwargs: Any) -> Callable:
    """Define a decorator for selecting output format."""

    def decorator(func: Union[Callable, click.Command]) -> Union[Callable, click.Command]:
        return click.option(
            '--format',
            'fmt',
            type=click.Choice(['json', 'table'], case_sensitive=False),
            default='json',
            show_default=True,
            help='Output format',
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


def json_parse(data: Optional[str], fallback: Optional[Any] = None) -> dict:
    if not data:
        return fallback if fallback is not None else {}
    try:
        parsed = json.loads(data)
        return parsed if isinstance(parsed, dict) else (fallback if fallback is not None else {})
    except Exception:
        return fallback if fallback is not None else {}


def read_json_input(
    data: Optional[str] = None,
    *,
    file: Union[None, str, pathlib.Path] = None,
    allow_stdin: bool = False,
) -> Any:
    """Load JSON from a string, file path, or stdin."""
    if file:
        path = pathlib.Path(file)
        if not path.exists():
            raise click.BadParameter(f'file not found: {path}')
        with path.open('r', encoding='utf-8') as f:
            return json.load(f)

    if data:
        try:
            return json.loads(data)
        except json.JSONDecodeError as err:
            raise click.BadParameter(f'invalid JSON: {err}') from err

    if allow_stdin and not sys.stdin.isatty():
        try:
            return json.load(sys.stdin)
        except json.JSONDecodeError as err:
            raise click.BadParameter(f'invalid JSON from stdin: {err}') from err

    return None


def echo_json(data: Any, *, indent: int = 2) -> None:
    click.echo(json.dumps(data, indent=indent, default=str))


def echo_table(rows: list[Mapping[str, Any]], *, columns: Optional[list[str]] = None) -> None:
    """Render a list of dicts as a Rich table."""
    if not rows:
        click.echo('[]')
        return

    cols = columns or list(rows[0].keys())
    table = Table(show_header=True, header_style='bold')
    for col in cols:
        table.add_column(str(col))

    for row in rows:
        table.add_row(*[str(row.get(c, '')) for c in cols])

    Console().print(table)


def print_output(data: Any, *, fmt: str = 'json', columns: Optional[list[str]] = None) -> None:
    if fmt == 'table' and isinstance(data, list) and (not data or isinstance(data[0], Mapping)):
        echo_table(data, columns=columns)
    else:
        echo_json(data)


def write_bytes(content: bytes, output: Optional[pathlib.Path], *, default_name: str = 'download.bin') -> pathlib.Path:
    """Write binary content to a file and return the path used."""
    path = output or pathlib.Path(default_name)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return path


def write_response_file(
    response: Any, output: Optional[pathlib.Path], *, default_name: str = 'download.bin'
) -> pathlib.Path:
    """Persist an SDK HttpResponse buffer (or bytes) to disk."""
    if isinstance(response, (bytes, bytearray)):
        content = bytes(response)
    else:
        content = getattr(response, 'buffer', None) or b''
        if not content and isinstance(getattr(response, 'data', None), (str, bytes)):
            data = response.data
            content = data.encode('utf-8') if isinstance(data, str) else data
    return write_bytes(content, output, default_name=default_name)


@contextmanager
def spinner(message: str = 'Working...') -> Iterator[None]:
    """Show a Rich spinner while a blocking operation runs."""
    console = Console(stderr=True)
    with Progress(
        SpinnerColumn(),
        TextColumn('[progress.description]{task.description}'),
        console=console,
        transient=True,
    ) as progress:
        progress.add_task(description=message, total=None)
        yield


@contextmanager
def progress_status(message: str = 'Working...') -> Iterator[Callable[[str], None]]:
    """Spinner that can update its status message while polling."""
    console = Console(stderr=True)
    with Progress(
        SpinnerColumn(),
        TextColumn('[progress.description]{task.description}'),
        console=console,
        transient=True,
    ) as progress:
        task_id = progress.add_task(description=message, total=None)

        def update(msg: str) -> None:
            progress.update(task_id, description=msg)

        yield update


def handle_error(err: Exception) -> None:
    """Print a friendly error and exit with code 1."""
    from cspark.sdk import SparkError

    console = Console(stderr=True)
    if isinstance(err, SparkError):
        console.print(f'[red]✗[/red] {err.message}')
    else:
        console.print(f'[red]✗[/red] {err}')
    raise click.exceptions.Exit(1) from err


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

        return None

    def resolve_command(self, ctx, args):
        # always return the command's name, not the alias
        _, cmd, args = super().resolve_command(ctx, args)
        return cmd.name, cmd, args  # type: ignore
